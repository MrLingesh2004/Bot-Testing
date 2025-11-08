"""
meal_recipe_bot.py
Single-file Meal Recipe Bot using TeleBot (PyTelegramBotAPI) + TheMealDB

Features:
- /start welcome
- /categories (Nx3) with pagination (edits same message)
- /cuisines (Nx3) with pagination (edits same message)
- /search <name>
- /random
- /favorites (save/view)
- View recipe details, save recipe from details
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import html
import json
import os
import urllib.parse

# ---------------- CONFIG ----------------
TELEGRAM_BOT_TOKEN = "7219661150:AAGDA-l3vGhSBdfhWnxb9XhNazd_NIpVXZA"   # <-- replace
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")

FAVORITES_FILE = "favorites.json"
ITEMS_PER_PAGE = 9   # 3x3 grid

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"

# ---------------- STORAGE ----------------
if not os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, "w") as f:
        json.dump({}, f)

def load_favorites():
    with open(FAVORITES_FILE, "r") as f:
        return json.load(f)

def save_favorites(data):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- DATA ----------------
# Predefined cuisines (extend as needed)
CUISINES = [
    "Indian","Chinese","Italian","Korean","Japanese","Thai","Mexican","French","Spanish",
    "American","Turkish","Greek","Vietnamese","Lebanese","Moroccan","Brazilian","Peruvian"
]

# ---------------- UTIL ----------------
def safe(text):
    return html.escape(text or "", quote=False)

def quote_cb(s: str) -> str:
    return urllib.parse.quote_plus(s)

def unquote_cb(s: str) -> str:
    return urllib.parse.unquote_plus(s)

# ---------------- MEALDB HELPERS ----------------
def get_categories():
    url = f"{MEALDB_BASE}/categories.php"
    r = requests.get(url)
    j = r.json()
    return [c["strCategory"] for c in j["categories"]]

def get_meals_by_category(category):
    url = f"{MEALDB_BASE}/filter.php?c={urllib.parse.quote_plus(category)}"
    r = requests.get(url); j = r.json()
    return j.get("meals") or []

def get_meals_by_cuisine(cuisine):
    url = f"{MEALDB_BASE}/filter.php?a={urllib.parse.quote_plus(cuisine)}"
    r = requests.get(url); j = r.json()
    return j.get("meals") or []

def get_meal_by_id(meal_id):
    url = f"{MEALDB_BASE}/lookup.php?i={urllib.parse.quote_plus(str(meal_id))}"
    r = requests.get(url); j = r.json()
    return j["meals"][0]

def search_meals_by_name(q):
    url = f"{MEALDB_BASE}/search.php?s={urllib.parse.quote_plus(q)}"
    r = requests.get(url); j = r.json()
    return j.get("meals") or []

def random_meal():
    url = f"{MEALDB_BASE}/random.php"
    r = requests.get(url); j = r.json()
    return j["meals"][0]

# ---------------- KEYBOARDS ----------------
def build_items_keyboard(items, prefix, page):
    """
    items: list of strings
    prefix: 'category' or 'cuisine' or 'search'
    page: zero-based page index
    """
    page_size = ITEMS_PER_PAGE
    total_pages = (len(items) + page_size - 1) // page_size or 1
    start = page * page_size
    page_items = items[start:start+page_size]

    kb = InlineKeyboardMarkup()
    row = []
    for item in page_items:
        q = quote_cb(item)
        row.append(InlineKeyboardButton(safe(item), callback_data=f"select:{prefix}:{q}:{page}"))
        if len(row) == 3:
            kb.add(*row); row = []
    if row:
        kb.add(*row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"nav:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if start + page_size < len(items):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav:{prefix}:{page+1}"))
    if nav:
        kb.row(*nav)
    return kb

def build_meals_keyboard(meals, mode, name, page):
    """
    meals: list of meal dicts from filter endpoints
    mode: 'category' or 'cuisine' or 'search'
    name: name string
    page: zero-based
    """
    page_size = ITEMS_PER_PAGE
    total_pages = (len(meals) + page_size - 1) // page_size or 1
    start = page * page_size
    page_meals = meals[start:start+page_size]

    kb = InlineKeyboardMarkup()
    row = []
    for m in page_meals:
        row.append(InlineKeyboardButton(safe(m["strMeal"]), callback_data=f"meal:{m['idMeal']}"))
        if len(row) == 3:
            kb.add(*row); row = []
    if row:
        kb.add(*row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"mealsnav:{mode}:{quote_cb(name)}:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if start + page_size < len(meals):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"mealsnav:{mode}:{quote_cb(name)}:{page+1}"))
    if nav:
        kb.row(*nav)

    back_label = "🔙 Back to Cuisines" if mode=="cuisine" else "🔙 Back to Categories"
    kb.add(InlineKeyboardButton(back_label, callback_data=f"back:{mode}"))
    return kb

def build_meal_actions(meal_id):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("💾 Save", callback_data=f"save:{meal_id}"),
        InlineKeyboardButton("🎲 Random", callback_data="random"),
        InlineKeyboardButton("🔙 Back to Menus", callback_data="back:menus")
    )
    return kb

# ---------------- SEND FUNCTIONS ----------------
def send_meal_details(chat_id, meal):
    caption = f"🍽 <b>{safe(meal.get('strMeal'))}</b>\n🏷 {safe(meal.get('strCategory','N/A'))} • 🌍 {safe(meal.get('strArea','N/A'))}"
    if meal.get("strMealThumb"):
        bot.send_photo(chat_id, meal["strMealThumb"], caption=caption)
    else:
        bot.send_message(chat_id, caption)

    # ingredients
    ingredients = "🧂 <b>Ingredients:</b>\n"
    for i in range(1,21):
        ing = meal.get(f"strIngredient{i}")
        meas = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ingredients += f"• {safe(ing)} — {safe(meas)}\n"
    instructions = f"\n🔥 <b>Instructions:</b>\n{safe(meal.get('strInstructions','N/A'))}"
    msg = ingredients + instructions
    for i in range(0, len(msg), 4000):
        bot.send_message(chat_id, msg[i:i+4000])
    bot.send_message(chat_id, "Actions:", reply_markup=build_meal_actions(meal["idMeal"]))

def open_main_menu(chat_id, text=None):
    text = text or ("👨‍🍳 <b>Welcome to MealRecipe Bot!</b>\nDiscover recipes from around the world. Choose a category or cuisine to begin.")
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🍱 Categories", callback_data="menu:categories:0"),
        InlineKeyboardButton("🌍 Cuisines", callback_data="menu:cuisines:0")
    )
    bot.send_message(chat_id, text, reply_markup=kb)

# ---------------- COMMANDS ----------------
@bot.message_handler(commands=['start'])
def cmd_start(msg):
    open_main_menu(msg.chat.id)

@bot.message_handler(commands=['categories'])
def cmd_categories(msg):
    cats = get_categories()
    kb = build_items_keyboard(cats, "category", 0)
    bot.send_message(msg.chat.id, "🍱 <b>Select a Category</b> (Page 1)", reply_markup=kb)

@bot.message_handler(commands=['cuisines'])
def cmd_cuisines(msg):
    kb = build_items_keyboard(CUISINES, "cuisine", 0)
    bot.send_message(msg.chat.id, "🌍 <b>Select a Cuisine</b> (Page 1)", reply_markup=kb)

@bot.message_handler(commands=['random'])
def cmd_random(msg):
    try:
        meal = random_meal()
        send_meal_details(msg.chat.id, meal)
    except Exception:
        bot.send_message(msg.chat.id, "⚠️ Could not fetch random recipe right now.")

@bot.message_handler(commands=['search'])
def cmd_search(msg):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(msg.chat.id, "❗ Usage: /search <recipe name>")
        return
    q = parts[1].strip()
    meals = search_meals_by_name(q)
    if not meals:
        bot.send_message(msg.chat.id, f"😔 No recipes found for «{safe(q)}».")
        return
    # show meals list using meal page UI — create names list to reuse build_items_keyboard
    names = [m["strMeal"] for m in meals]
    kb = build_items_keyboard(names, "search", 0)
    bot.send_message(msg.chat.id, f"🔎 Results for «{safe(q)}» — choose:", reply_markup=kb)

@bot.message_handler(commands=['favorites'])
def cmd_favorites(msg):
    favs = load_favorites()
    user = str(msg.chat.id)
    if user not in favs or not favs[user]:
        bot.send_message(msg.chat.id, "💔 You have no saved recipes yet.")
        return
    kb = InlineKeyboardMarkup(); row=[]
    for idx, mid in enumerate(favs[user], start=1):
        try:
            meal = get_meal_by_id(mid)
            row.append(InlineKeyboardButton(safe(meal["strMeal"]), callback_data=f"meal:{mid}"))
        except Exception:
            continue
        if len(row) == 3:
            kb.add(*row); row=[]
    if row: kb.add(*row)
    bot.send_message(msg.chat.id, "💖 Your favorites:", reply_markup=kb)

# ---------------- CALLBACK HANDLER ----------------
@bot.callback_query_handler(func=lambda call: True)
def callback_all(call):
    data = call.data or ""
    # noop
    if data == "noop":
        bot.answer_callback_query(call.id, "")
        return

    # top menu navigation
    if data.startswith("menu:"):
        _, menu_type, page = data.split(":")
        page = int(page)
        if menu_type == "categories":
            cats = get_categories()
            kb = build_items_keyboard(cats, "category", page)
            bot.edit_message_text(f"🍱 <b>Select a Category</b> (Page {page+1})", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        else:
            kb = build_items_keyboard(CUISINES, "cuisine", page)
            bot.edit_message_text(f"🌍 <b>Select a Cuisine</b> (Page {page+1})", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    # nav for items (categories/cuisines/search)
    if data.startswith("nav:"):
        _, prefix, page = data.split(":")
        page = int(page)
        if prefix == "category":
            cats = get_categories()
            kb = build_items_keyboard(cats, "category", page)
            bot.edit_message_text(f"🍱 <b>Select a Category</b> (Page {page+1})", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        elif prefix == "cuisine":
            kb = build_items_keyboard(CUISINES, "cuisine", page)
            bot.edit_message_text(f"🌍 <b>Select a Cuisine</b> (Page {page+1})", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        elif prefix == "search":
            # This simple implementation shows names page; selecting a name triggers search->detail
            kb = build_items_keyboard([], "search", page)
            bot.edit_message_text(f"🔎 Search results (Page {page+1})", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    # select an item (category/cuisine/search)
    if data.startswith("select:"):
        try:
            _, prefix, quoted_item, page = data.split(":",3)
            item = unquote_cb(quoted_item)
        except Exception:
            bot.answer_callback_query(call.id, "Invalid selection.")
            return

        if prefix == "category":
            meals = get_meals_by_category(item)
            if not meals:
                bot.answer_callback_query(call.id, "No recipes found in this category.")
                return
            kb = build_meals_keyboard(meals, "category", item, 0)
            bot.edit_message_text(f"🍴 <b>{safe(item)}</b> — recipes (Page 1)", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
            return

        if prefix == "cuisine":
            meals = get_meals_by_cuisine(item)
            if not meals:
                bot.answer_callback_query(call.id, "No recipes found for this cuisine.")
                return
            kb = build_meals_keyboard(meals, "cuisine", item, 0)
            bot.edit_message_text(f"🌏 <b>{safe(item)}</b> — recipes (Page 1)", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
            return

        if prefix == "search":
            # find the first meal by name and show details
            results = search_meals_by_name(item)
            if not results:
                bot.answer_callback_query(call.id, "No recipe details found.")
                return
            send_meal_details(call.message.chat.id, results[0])
            return

    # mealsnav: pagination within the meal list
    if data.startswith("mealsnav:"):
        try:
            _, mode, quoted_name, page = data.split(":",3)
            name = unquote_cb(quoted_name); page = int(page)
        except Exception:
            bot.answer_callback_query(call.id, "Invalid navigation data.")
            return
        if mode == "cuisine":
            meals = get_meals_by_cuisine(name)
        else:
            meals = get_meals_by_category(name)
        kb = build_meals_keyboard(meals, mode, name, page)
        bot.edit_message_text((f"🌏 <b>{safe(name)}</b> — recipes (Page {page+1})" if mode=="cuisine" else f"🍴 <b>{safe(name)}</b> — recipes (Page {page+1})"), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    # meal details
    if data.startswith("meal:"):
        _, meal_id = data.split(":",1)
        try:
            meal = get_meal_by_id(meal_id)
            send_meal_details(call.message.chat.id, meal)
        except Exception:
            bot.answer_callback_query(call.id, "Failed to load recipe details.")
        return

    # save favorite
    if data.startswith("save:"):
        _, meal_id = data.split(":",1)
        favs = load_favorites()
        user = str(call.message.chat.id)
        if user not in favs:
            favs[user] = []
        if meal_id not in favs[user]:
            favs[user].append(meal_id)
            save_favorites(favs)
            bot.answer_callback_query(call.id, "💾 Saved to favorites.")
        else:
            bot.answer_callback_query(call.id, "⚠️ Already in favorites.")
        return

    # back buttons
    if data.startswith("back:"):
        _, mode = data.split(":",1)
        try:
            if mode == "menus":
                kb = InlineKeyboardMarkup()
                kb.row(InlineKeyboardButton("🍱 Categories", callback_data="menu:categories:0"), InlineKeyboardButton("🌍 Cuisines", callback_data="menu:cuisines:0"))
                bot.edit_message_text("👨‍🍳 <b>MealRecipe</b>\nChoose a browse mode:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
            elif mode == "cuisine":
                kb = build_items_keyboard(CUISINES, "cuisine", 0)
                bot.edit_message_text("🌍 <b>Select a Cuisine</b> (Page 1)", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
            else:
                cats = get_categories()
                kb = build_items_keyboard(cats, "category", 0)
                bot.edit_message_text("🍱 <b>Select a Category</b> (Page 1)", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        except Exception:
            pass
        return

    # random button
    if data == "random":
        try:
            meal = random_meal()
            send_meal_details(call.message.chat.id, meal)
        except Exception:
            bot.answer_callback_query(call.id, "Failed to fetch random recipe.")
        return

    bot.answer_callback_query(call.id, "Unknown action.")

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🚀 MealRecipe Bot running...")
    bot.infinity_polling()