import telebot, requests, random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

Token = ''
bot = telebot.TeleBot(Token, parse_mode='HTML')

categories = ['Romantic', 'Funny', 'Cheesy', 'Flirty', 'Clever', 'Complimentary']

# Function to create category keyboard
def fetch_categories():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(*[InlineKeyboardButton(category, callback_data=category) for category in categories])
    return '✨ Explore with these categories:', kb

# Fetch a random pickup line
def random_line():
    res = requests.get('https://rizzapi.vercel.app/random').json()
    text = res['text']
    category = res['category']
    return f'💬 <b>Category:</b> {category}\n\n{text}'

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ('📚 Categories', 'categories'),
        ('🎲 Random', 'random')
    ]
    kb.add(*[InlineKeyboardButton(text, callback_data=data) for text, data in buttons])
    bot.send_message(message.chat.id, "Hey there! 👋\nChoose an option below:", reply_markup=kb)

# Handle callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # Show categories
    if data == 'categories':
        text, kb = fetch_categories()
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=kb
        )

    # Show random pickup line
    elif data == 'random':
        text = random_line()
        bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=msg_id
        )

    # Show specific category line
    elif data in categories:
        res = requests.get(f'https://rizzapi.vercel.app/category/{data}').json()
        key = random.randint(0, len(res) - 1)
        text = res[key]['text']
        bot.edit_message_text(
            f'💬 <b>Category:</b> {res[key]["category"]}\n\n{text}',
            chat_id=chat_id,
            message_id=msg_id
        )

if __name__ == '__main__':
    print('🚀 Pick-up Lines Bot is Running...')
    bot.infinity_polling()
