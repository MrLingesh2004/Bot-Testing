import requests, random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler
)

categories = ['Romantic', 'Funny', 'Cheesy', 'Flirty', 'Clever', 'Complimentary']


async def open_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None):
    chat_id = update.effective_chat.id
    text = text or 'Hey there! 👋\nChoose an option below:'
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Categories", callback_data="categories"),
         InlineKeyboardButton("🎲 Random", callback_data="random")]
    ])
    await context.bot.send_message(chat_id, text, reply_markup=kb, parse_mode='HTML')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await open_main_menu(update, context)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    await query.answer()

    if data == 'categories':
        # Correct way to build buttons in python-telegram-bot
        keyboard = [
            [InlineKeyboardButton(categories[0], callback_data=categories[0]),
             InlineKeyboardButton(categories[1], callback_data=categories[1])],
            [InlineKeyboardButton(categories[2], callback_data=categories[2]),
             InlineKeyboardButton(categories[3], callback_data=categories[3])],
            [InlineKeyboardButton(categories[4], callback_data=categories[4]),
             InlineKeyboardButton(categories[5], callback_data=categories[5])]
        ]

        kb = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='✨ Explore with these <b>categories:</b>',
            reply_markup=kb,
            parse_mode='HTML'
        )
        
        
    elif data == 'random':
        result = requests.get('https://rizzapi.vercel.app/random').json()
        res = result['text']
        category = result['category']
        text = f'💬 <b>Category:</b> {category}\n\n{res}'
        await query.edit_message_text(
            text = text,
            parse_mode='HTML'
        )


    elif data in categories:
        res = requests.get(f'https://rizzapi.vercel.app/category/{data}').json()
        key = random.randint(0, len(res) - 1)
        text = res[key]['text']
        await query.edit_message_text(
            text = f'💬 <b>Category:</b> {res[key]["category"]}\n\n{text}',
            parse_mode='HTML'
        )


Token = ''

def main():
    app = ApplicationBuilder().token(Token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
