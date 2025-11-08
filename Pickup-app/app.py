from flask import (
    Flask, render_template, redirect, url_for, session,
    request, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests, random, urllib.parse

from models import db, User, Bookmark

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pickup.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# ---------------------
# Allowed pickup line categories
# ---------------------
BASE_API_URL = "https://rizzapi.vercel.app/category/"
ALLOWED_CATEGORIES = {
    "Romantic", "Flirty", "Cheesy", "Funny", "Smooth", "Cute", "Nerd",
    "Food", "Dirty", "Pokemon", "Anime", "Valentine", "Bad", "Corny"
}

# ---------------------
# Helpers
# ---------------------
def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.args.get("xhr"):
                return jsonify({"error": "Unauthorized"}), 401
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

# ---------------------
# Initialize DB
# ---------------------
def create_tables():
    db.create_all()

# ---------------------
# Public routes
# ---------------------
@app.route("/")
def index():
    return render_template("pages/index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("pages/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return render_template("pages/register.html")

        hashed = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        flash("Registration successful!", "success")
        return redirect(url_for("dashboard"))

    return render_template("pages/register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return render_template("pages/login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("pages/login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ---------------------
# Dashboard & bookmarks
# ---------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    bookmarks = Bookmark.query.filter_by(user_id=user.id).order_by(Bookmark.id.desc()).all()
    return render_template("pages/dashboard.html", user=user, bookmarks=bookmarks)

@app.route("/bookmarks")
@login_required
def bookmarks_page():
    user = current_user()
    bookmarks = Bookmark.query.filter_by(user_id=user.id).order_by(Bookmark.id.desc()).all()
    return render_template("pages/bookmarks.html", bookmarks=bookmarks)

@app.route("/bookmark", methods=["POST"])
@login_required
def bookmark():
    user = current_user()
    if request.is_json:
        payload = request.get_json()
        line = payload.get("line", "").strip()
        category = payload.get("category", "").strip()
    else:
        line = request.form.get("line", "").strip()
        category = request.form.get("category", "").strip()

    if not line:
        return jsonify({"status": "error", "message": "Empty line"}), 400

    bm = Bookmark(line_text=line[:1000], category=category[:100], user_id=user.id)
    db.session.add(bm)
    db.session.commit()
    return jsonify({"status": "success", "id": bm.id})

@app.route("/bookmark/delete", methods=["POST"])
@login_required
def bookmark_delete():
    user = current_user()
    if request.is_json:
        payload = request.get_json()
        bid = payload.get("id")
    else:
        bid = request.form.get("id")

    if not bid:
        return jsonify({"status": "error", "message": "Missing id"}), 400

    bm = Bookmark.query.get(bid)
    if not bm or bm.user_id != user.id:
        return jsonify({"status": "error", "message": "Not found or unauthorized"}), 404

    db.session.delete(bm)
    db.session.commit()
    return jsonify({"status": "success"})

# ---------------------
# Pickup line generator
# ---------------------
@app.route("/generate", methods=["GET"])
@login_required
def generate():
    category = request.args.get("category", "Romantic").strip()
    cat = category.title()
    if cat not in ALLOWED_CATEGORIES:
        cat = category

    cat_quoted = urllib.parse.quote_plus(cat)
    api_url = f"{BASE_API_URL}{cat_quoted}"

    try:
        resp = requests.get(api_url, timeout=6)
        if resp.status_code != 200:
            return jsonify({"text": f"Failed to fetch: {resp.status_code}", "category": cat}), resp.status_code

        data = resp.json()
        if isinstance(data, list) and data:
            chosen = random.choice(data)
        elif isinstance(data, dict):
            chosen = data
        else:
            return jsonify({"text": "No lines found 😅", "category": cat})

        text = chosen.get("text") or chosen.get("line") or chosen.get("pickup") or ""
        if not text:
            return jsonify({"text": "Unexpected API response", "category": cat}), 502

        return jsonify({"text": text, "category": chosen.get("category", cat)})
    except requests.RequestException as e:
        return jsonify({"text": f"API request failed: {e}", "category": cat}), 502
    except Exception as e:
        return jsonify({"text": f"Internal error: {e}", "category": cat}), 500

# ---------------------
# API endpoint to list bookmarks
# ---------------------
@app.route("/api/bookmarks")
@login_required
def api_list_bookmarks():
    user = current_user()
    bms = Bookmark.query.filter_by(user_id=user.id).order_by(Bookmark.id.desc()).all()
    payload = [{"id": b.id, "line": b.line_text, "category": b.category} for b in bms]
    return jsonify(payload)

# ---------------------
# Run app
# ---------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)