import requests, json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

Token = ''
API_KEY = ''

f = open('modes.json', 'r')
MODES = json.load(f)
user_modes = {}

def get_response(prompt, model='gpt-3.5-turbo', mode_key=None):
    mode = MODES.get(mode_key, {})
    url = 'https://openrouter.ai/api/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
         'content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': mode.get('content', 'You are a helpful assistant')},
            {'role': 'user', 'content': prompt},    
        ]   
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        return f'Error {response.status_code}: {response.text}'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Hello {update.chat.username}!\n'
        "I'm your personal AI Assistant!\n"
    )
    
    
async def helper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Helper Command!!')
    
    
async def modes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    available = "\n".join([f"• {v['name']} — {k}" for k, v in MODES.items()])
    parts = update.message.text.split(maxsplit=1)
    mode_key = ''
    
    if len(parts) == 2:
        mode_key = parts[1].lower().strip()
        
        if MODES.get(mode_key):
            user_modes[update.message.chat.id] = mode_key  # save user mode
            await update.message.reply_text(f"✅ Mode <b>{MODES[mode_key]['name']}</b> set successfully!",parse_mode='HTML')
        else:
            await update.message.reply_text('❌ Invalid mode. Use /mode to see all options.')
            
    else:
        await update.message.reply_text(f"Please choose a mode:\n{available}\n\nUsage: /mode friend",parse_mode='HTML')
    
    
async def query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    mode_key = user_modes.get(update.message.chat.id)
    response = get_response(prompt, mode_key=mode_key)
    await update.message.reply_text(response)
    
app = ApplicationBuilder().token(Token).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('help', helper))
app.add_handler(CommandHandler('mode', modes))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, query_handler))

print('OpenRouter Telegram Bot is Running....')
app.run_polling()
