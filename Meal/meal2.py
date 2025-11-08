# meal_recipe_bot_ptb_full.py
"""
Full Meal Recipe Bot using python-telegram-bot (v20+) + TheMealDB
Features:
 - /start, /categories, /cuisines, /search, /random, /favorites
 - Nx3 inline keyboards with pagination that EDIT the same message
 - Recipe details, Save to favorites
 - Step-by-step instructions with Next/Prev (edits the same step message)
 - Persistent favorites.json per chat
"""

import os
import json
import html
import urllib.parse
import logging
import requests
from typing import List, Dict, Any, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = ""  # <-- set your token here
MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
FAVORITES_FILE = "favorites.json"
ITEMS_PER_PAGE = 9  # 3x3 layout
# Predefined cuisines list (extendable)
CUISINES = [
    "Indian","Chinese","Italian","Korean","Japanese","Thai","Mexican","French","Spanish",
    "American","Turkish","Greek","Vietnamese","Lebanese","Moroccan","Brazilian","Peruvian"
]

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- STORAGE ----------------
if not os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, "w") as f:
        json.dump({}, f)

def load_favorites() -> Dict[str, List[str]]:
    with open(FAVORITES_FILE, "r") as f:
        return json.load(f)

def save_favorites(data: Dict[str, List[str]]):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- UTIL ----------------
def safe(text: Optional[str]) -> str:
    return html.escape(text or "", quote=False)

def quote_cb(s: str) -> str:
    return urllib.parse.quote_plus(s)

def unquote_cb(s: str) -> str:
    return urllib.parse.unquote_plus(s)

# ---------------- MEALDB HELPERS ----------------
def get_categories() -> List[str]:
    try:
        r = requests.get(f"{MEALDB_BASE}/categories.php", timeout=10)
        j = r.json()
        return [c["strCategory"] for c in j.get("categories", [])]
    except Exception as e:
        logger.exception("get_categories failed")
        return []

def get_meals_by_category(category: str) -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{MEALDB_BASE}/filter.php?c={urllib.parse.quote_plus(category)}", timeout=10)
        j = r.json()
        return j.get("meals") or []
    except Exception:
        logger.exception("get_meals_by_category failed")
        return []

def get_meals_by_cuisine(cuisine: str) -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{MEALDB_BASE}/filter.php?a={urllib.parse.quote_plus(cuisine)}", timeout=10)
        j = r.json()
        return j.get("meals") or []
    except Exception:
        logger.exception("get_meals_by_cuisine failed")
        return []

def get_meal_by_id(meal_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{MEALDB_BASE}/lookup.php?i={urllib.parse.quote_plus(str(meal_id))}", timeout=10)
        j = r.json()
        meals = j.get("meals")
        return meals[0] if meals else None
    except Exception:
        logger.exception("get_meal_by_id failed")
        return None

def search_meals_by_name(q: str) -> List[Dict[str, Any]]:
    try:
        r = requests.get(f"{MEALDB_BASE}/search.php?s={urllib.parse.quote_plus(q)}", timeout=10)
        j = r.json()
        return j.get("meals") or []
    except Exception:
        logger.exception("search_meals_by_name failed")
        return []

def random_meal() -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(f"{MEALDB_BASE}/random.php", timeout=10)
        j = r.json()
        meals = j.get("meals")
        return meals[0] if meals else None
    except Exception:
        logger.exception("random_meal failed")
        return None

# ---------------- KEYBOARDS ----------------
def build_items_keyboard(items: List[str], prefix: str, page: int) -> InlineKeyboardMarkup:
    page_size = ITEMS_PER_PAGE
    total_pages = (len(items) + page_size - 1) // page_size or 1
    start = page * page_size
    page_items = items[start:start + page_size]

    kb_rows = []
    row = []
    for item in page_items:
        q = quote_cb(item)
        row.append(InlineKeyboardButton(safe(item), callback_data=f"select:{prefix}:{q}:{page}"))
        if len(row) == 3:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"nav:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if start + page_size < len(items):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav:{prefix}:{page+1}"))
    if nav:
        kb_rows.append(nav)

    return InlineKeyboardMarkup(kb_rows)

def build_meals_keyboard(meals: List[Dict[str,Any]], mode: str, name: str, page: int) -> InlineKeyboardMarkup:
    page_size = ITEMS_PER_PAGE
    total_pages = (len(meals) + page_size - 1) // page_size or 1
    start = page * page_size
    page_meals = meals[start:start + page_size]

    kb_rows = []
    row = []
    for m in page_meals:
        row.append(InlineKeyboardButton(safe(m["strMeal"]), callback_data=f"meal:{m['idMeal']}"))
        if len(row) == 3:
            kb_rows.append(row)
            row = []
    if row:
        kb_rows.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"mealsnav:{mode}:{quote_cb(name)}:{page-1}"))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if start + page_size < len(meals):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"mealsnav:{mode}:{quote_cb(name)}:{page+1}"))
    if nav:
        kb_rows.append(nav)

    back_label = "🔙 Back to Cuisines" if mode == "cuisine" else "🔙 Back to Categories"
    kb_rows.append([InlineKeyboardButton(back_label, callback_data=f"back:{mode}")])
    return InlineKeyboardMarkup(kb_rows)

def build_detail_actions(meal_id: str) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton("💾 Save", callback_data=f"save:{meal_id}"),
            InlineKeyboardButton("📖 View Steps", callback_data=f"viewsteps:{meal_id}"),
            InlineKeyboardButton("🎲 Random", callback_data="random")
        ],
        [InlineKeyboardButton("🔙 Back to Menus", callback_data="back:menus")]
    ]
    return InlineKeyboardMarkup(kb)

def build_step_nav(step_index: int, total: int, recipe_key: str) -> InlineKeyboardMarkup:
    row = []
    if step_index > 0:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"stepnav:{recipe_key}:{step_index-1}"))
    row.append(InlineKeyboardButton(f"Step {step_index+1}/{total}", callback_data="noop"))
    if step_index < total - 1:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"stepnav:{recipe_key}:{step_index+1}"))
    return InlineKeyboardMarkup([row])

# ---------------- SESSION STORAGE (in-memory) ----------------
# sessions[chat_id] = { 'steps': [...], 'step_msg_id': int, 'recipe_key': str }
sessions: Dict[str, Dict[str,Any]] = {}

# ---------------- SEND / UI FUNCTIONS ----------------
async def open_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: Optional[str]=None):
    chat_id = update.effective_chat.id
    text = text or ("👨‍🍳 <b>Welcome to MealRecipe Bot!</b>\nDiscover recipes from around the world. Choose a category or cuisine to begin.")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🍱 Categories", callback_data="menu:categories:0"),
                                InlineKeyboardButton("🌍 Cuisines", callback_data="menu:cuisines:0")]])
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb, parse_mode="HTML")

async def send_meal_details(chat_id: int, context: ContextTypes.DEFAULT_TYPE, meal: Dict[str,Any]):
    # send photo with caption (short)
    caption = f"🍽 <b>{safe(meal.get('strMeal'))}</b>\n🏷 {safe(meal.get('strCategory','N/A'))} • 🌍 {safe(meal.get('strArea','N/A'))}"
    if meal.get("strMealThumb"):
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=meal["strMealThumb"], caption=caption, parse_mode="HTML")
        except Exception:
            # fallback to text
            await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")

    # Prepare ingredients + short instructions snippet as a follow-up message (so steps can be viewed separately)
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        meas = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ingredients.append(f"• {safe(ing)} — {safe(meas)}")
    ing_text = "🧂 <b>Ingredients:</b>\n" + ("\n".join(ingredients) if ingredients else "N/A")
    # show only first 900 characters of instructions in the details message to avoid caption limits
    instr = meal.get("strInstructions", "")
    instr_preview = instr.strip()[:900] + ("..." if len(instr.strip()) > 900 else "")
    details_text = ing_text + "\n\n🔥 <b>Instructions (preview):</b>\n" + safe(instr_preview)

    # actions keyboard includes "View Steps" which will create a step session & message
    await context.bot.send_message(chat_id=chat_id, text=details_text, parse_mode="HTML", reply_markup=build_detail_actions(meal["idMeal"]))

# ---------------- HANDLERS ----------------
# /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await open_main_menu(update, context)

# /categories
async def categories_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cats = get_categories()
    if not cats:
        await update.message.reply_text("⚠️ Could not fetch categories right now.")
        return
    kb = build_items_keyboard(cats, "category", 0)
    await update.message.reply_html("🍱 <b>Select a Category</b> (Page 1)", reply_markup=kb)

# /cuisines
async def cuisines_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = build_items_keyboard(CUISINES, "cuisine", 0)
    await update.message.reply_html("🌍 <b>Select a Cuisine</b> (Page 1)", reply_markup=kb)

# /random
async def random_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meal = random_meal()
    if not meal:
        await update.message.reply_text("⚠️ Could not fetch a random recipe.")
        return
    await send_meal_details(update.effective_chat.id, context, meal)

# /search
async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Usage: /search <recipe name>")
        return
    q = " ".join(context.args).strip()
    meals = search_meals_by_name(q)
    if not meals:
        await update.message.reply_html(f"😔 No recipes found for «{safe(q)}».")
        return
    # show names page using build_items_keyboard
    names = [m["strMeal"] for m in meals]
    kb = build_items_keyboard(names, "search", 0)
    await update.message.reply_html(f"🔎 Results for «{safe(q)}» — choose:", reply_markup=kb)

# /favorites
async def favorites_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    favs = load_favorites()
    user = str(update.effective_chat.id)
    if user not in favs or not favs[user]:
        await update.message.reply_text("💔 You have no saved recipes yet.")
        return
    kb_rows = []
    row = []
    for mid in favs[user]:
        meal = get_meal_by_id(mid)
        if not meal:
            continue
        row.append(InlineKeyboardButton(safe(meal["strMeal"]), callback_data=f"meal:{mid}"))
        if len(row) == 3:
            kb_rows.append(row); row = []
    if row:
        kb_rows.append(row)
    await update.message.reply_html("💖 Your favorites:", reply_markup=InlineKeyboardMarkup(kb_rows))

# Universal callback handler
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    data = query.data
    await query.answer()

    # noop (page indicator)
    if data == "noop":
        return

    # menu:categories|cuisines pagination (edits same message)
    if data.startswith("menu:"):
        try:
            _, menu_type, page_str = data.split(":")
            page = int(page_str)
            if menu_type == "categories":
                cats = get_categories()
                kb = build_items_keyboard(cats, "category", page)
                await query.edit_message_text(f"🍱 <b>Select a Category</b> (Page {page+1})", reply_markup=kb, parse_mode="HTML")
            else:
                kb = build_items_keyboard(CUISINES, "cuisine", page)
                await query.edit_message_text(f"🌍 <b>Select a Cuisine</b> (Page {page+1})", reply_markup=kb, parse_mode="HTML")
        except Exception:
            logger.exception("menu callback error")
            await query.answer("⚠️ Error loading menu.")
        return

    # nav: categories/cuisines/search pagination
    if data.startswith("nav:"):
        try:
            _, prefix, page_str = data.split(":")
            page = int(page_str)
            if prefix == "category":
                cats = get_categories()
                kb = build_items_keyboard(cats, "category", page)
                await query.edit_message_text(f"🍱 <b>Select a Category</b> (Page {page+1})", reply_markup=kb, parse_mode="HTML")
            elif prefix == "cuisine":
                kb = build_items_keyboard(CUISINES, "cuisine", page)
                await query.edit_message_text(f"🌍 <b>Select a Cuisine</b> (Page {page+1})", reply_markup=kb, parse_mode="HTML")
            elif prefix == "search":
                # For search pagination you'd have to keep results in session - simple placeholder:
                await query.edit_message_text(f"🔎 Search results (Page {page+1})", parse_mode="HTML")
        except Exception:
            logger.exception("nav callback error")
            await query.answer("⚠️ Navigation error.")
        return

    # select:prefix:quoted_item:page  -> category/cuisine/search selection
    if data.startswith("select:"):
        try:
            _, prefix, quoted_item, page_str = data.split(":", 3)
            item = unquote_cb(quoted_item)
            if prefix == "category":
                meals = get_meals_by_category(item)
                if not meals:
                    await query.answer("No recipes found in this category.")
                    return
                kb = build_meals_keyboard(meals, "category", item, 0)
                await query.edit_message_text(f"🍴 <b>{safe(item)}</b> — recipes (Page 1)", reply_markup=kb, parse_mode="HTML")
                return
            if prefix == "cuisine":
                meals = get_meals_by_cuisine(item)
                if not meals:
                    await query.answer("No recipes found for this cuisine.")
                    return
                kb = build_meals_keyboard(meals, "cuisine", item, 0)
                await query.edit_message_text(f"🌏 <b>{safe(item)}</b> — recipes (Page 1)", reply_markup=kb, parse_mode="HTML")
                return
            if prefix == "search":
                # select a name from search; attempt to fetch by name and show first match
                results = search_meals_by_name(item)
                if not results:
                    await query.answer("No recipe details found.")
                    return
                meal = results[0]
                await send_meal_details(query.message.chat.id, context, meal)
                return
        except Exception:
            logger.exception("select callback error")
            await query.answer("⚠️ Selection error.")
        return

    # mealsnav: pagination within meals list
    if data.startswith("mealsnav:"):
        try:
            _, mode, quoted_name, page_str = data.split(":", 3)
            name = unquote_cb(quoted_name)
            page = int(page_str)
            if mode == "cuisine":
                meals = get_meals_by_cuisine(name)
            else:
                meals = get_meals_by_category(name)
            kb = build_meals_keyboard(meals, mode, name, page)
            title = (f"🌏 <b>{safe(name)}</b> — recipes (Page {page+1})" if mode == "cuisine"
                     else f"🍴 <b>{safe(name)}</b> — recipes (Page {page+1})")
            await query.edit_message_text(title, reply_markup=kb, parse_mode="HTML")
        except Exception:
            logger.exception("mealsnav callback error")
            await query.answer("⚠️ Meals navigation error.")
        return

    # meal:{id} -> show meal details (sends new messages: photo + details + actions)
    if data.startswith("meal:"):
        try:
            _, meal_id = data.split(":", 1)
            meal = get_meal_by_id(meal_id)
            if not meal:
                await query.answer("⚠️ Failed to load recipe.")
                return
            await send_meal_details(query.message.chat.id, context, meal)
        except Exception:
            logger.exception("meal callback error")
            await query.answer("⚠️ Error loading meal.")
        return

    # save:{id}
    if data.startswith("save:"):
        try:
            _, meal_id = data.split(":", 1)
            favs = load_favorites()
            user = str(query.message.chat.id)
            if user not in favs:
                favs[user] = []
            if meal_id not in favs[user]:
                favs[user].append(meal_id)
                save_favorites(favs)
                await query.answer("💾 Saved to favorites.")
            else:
                await query.answer("⚠️ Already in favorites.")
        except Exception:
            logger.exception("save callback error")
            await query.answer("⚠️ Could not save.")
        return

    # viewsteps:{meal_id} -> create session and send step message (first step)
    if data.startswith("viewsteps:"):
        try:
            _, meal_id = data.split(":",1)
            meal = get_meal_by_id(meal_id)
            if not meal:
                await query.answer("⚠️ Cannot fetch recipe steps.")
                return

            # parse instructions into steps (split by line breaks, then by sentence if needed)
            instr = meal.get("strInstructions", "").strip()
            # split into paragraphs first
            raw_steps = [p.strip() for p in instr.split("\n\n") if p.strip()]
            # if only one paragraph, split into sentences (naive)
            steps: List[str] = []
            if len(raw_steps) <= 1:
                # split by sentences (.!?)
                import re
                sentences = re.split(r'(?<=[.!?])\s+', instr)
                steps = [s.strip() for s in sentences if s.strip()]
            else:
                steps = raw_steps

            if not steps:
                await query.answer("⚠️ No steps available.")
                return

            # create session (per chat)
            chat_id = query.message.chat.id
            # send initial step message (so we can edit it later)
            step_index = 0
            step_text = f"🔥 <b>Step {step_index+1}/{len(steps)}</b>\n\n{safe(steps[step_index])}"
            sent = await context.bot.send_message(chat_id=chat_id, text=step_text, parse_mode="HTML",
                                                  reply_markup=build_step_nav(step_index, len(steps), meal_id))
            # store session info
            sessions[str(chat_id)] = {
                "steps": steps,
                "step_msg_id": sent.message_id,
                "meal_id": meal_id
            }
            # answer callback
            await query.answer()
        except Exception:
            logger.exception("viewsteps callback error")
            await query.answer("⚠️ Failed to open steps.")
        return
        
    # step navigation: stepnav:meal_id:step_index
    if data.startswith("stepnav:"):
        try:
            _, recipe_key, step_index_str = data.split(":",2)
            step_index = int(step_index_str)
            chat_id = str(query.message.chat.id)
            session = sessions.get(chat_id)
            if not session or session.get("meal_id") != recipe_key:
                # session could be missing if restarted, try to rebuild from meal id
                meal = get_meal_by_id(recipe_key)
                if not meal:
                    await query.answer("⚠️ Session expired.")
                    return
                instr = meal.get("strInstructions","").strip()
                raw_steps = [p.strip() for p in instr.split("\n\n") if p.strip()]
                if len(raw_steps) <= 1:
                    import re
                    sentences = re.split(r'(?<=[.!?])\s+', instr)
                    steps = [s.strip() for s in sentences if s.strip()]
                else:
                    steps = raw_steps
                session = {"steps": steps, "meal_id": recipe_key, "step_msg_id": query.message.message_id}
                sessions[chat_id] = session

            steps = session["steps"]
            step_index = max(0, min(step_index, len(steps)-1))
            session["current"] = step_index

            text = f"🔥 <b>Step {step_index+1}/{len(steps)}</b>\n\n{safe(steps[step_index])}"
            # edit the previously sent step message (use message_id from session if available)
            step_msg_id = session.get("step_msg_id") or query.message.message_id
            try:
                await context.bot.edit_message_text(text=text, chat_id=query.message.chat.id, message_id=step_msg_id,
                                                    parse_mode="HTML", reply_markup=build_step_nav(step_index, len(steps), recipe_key))
                await query.answer()
            except Exception:
                # fallback: edit current message
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=build_step_nav(step_index, len(steps), recipe_key))
                await query.answer()
        except Exception:
            logger.exception("stepnav callback error")
            await query.answer("⚠️ Step navigation error.")
        return

    # random
    if data == "random":
        meal = random_meal()
        if not meal:
            await query.answer("⚠️ Could not fetch random recipe.")
            return
        await send_meal_details(query.message.chat.id, context, meal)
        return
        
    # back:
    if data.startswith("back:"):
        try:
            _, mode = data.split(":",1)
            if mode == "menus":
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🍱 Categories", callback_data="menu:categories:0"),
                                            InlineKeyboardButton("🌍 Cuisines", callback_data="menu:cuisines:0")]])
                await query.edit_message_text("👨‍🍳 <b>MealRecipe</b>\nChoose a browse mode:", reply_markup=kb, parse_mode="HTML")
            elif mode == "cuisine":
                kb = build_items_keyboard(CUISINES, "cuisine", 0)
                await query.edit_message_text("🌍 <b>Select a Cuisine</b> (Page 1)", reply_markup=kb, parse_mode="HTML")
            else:
                cats = get_categories()
                kb = build_items_keyboard(cats, "category", 0)
                await query.edit_message_text("🍱 <b>Select a Category</b> (Page 1)", reply_markup=kb, parse_mode="HTML")
        except Exception:
            logger.exception("back callback error")
            await query.answer("⚠️ Back navigation failed.")
        return

    # fallback
    await query.answer("Unknown action.")

# message handler for free text — default route: treat as search
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    # treat as search query
    meals = search_meals_by_name(text)
    if not meals:
        await update.message.reply_text("😔 No recipes found. Try another search.")
        return
    # show names (build list)
    names = [m["strMeal"] for m in meals]
    kb = build_items_keyboard(names, "search", 0)
    await update.message.reply_html(f"🔎 Results for «{safe(text)}» — choose:", reply_markup=kb)    
        
# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("categories", categories_handler))
    app.add_handler(CommandHandler("cuisines", cuisines_handler))
    app.add_handler(CommandHandler("random", random_handler))
    app.add_handler(CommandHandler("search", search_handler))
    app.add_handler(CommandHandler("favorites", favorites_handler))

    # callbacks & messages
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    logger.info("🚀 MealRecipe Bot (python-telegram-bot) is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
