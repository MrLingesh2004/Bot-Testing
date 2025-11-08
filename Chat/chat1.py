import telebot, requests, json


Token = ''
API_KEY = ''
bot = telebot.TeleBot(Token, parse_mode='HTML')


f = open('modes.json', 'r')
MODES = json.load(f)
user_modes = {}


def fetch_answer(text, model='gpt-3.5-turbo', mode_key=None):
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
            {'role': 'user', 'content': text},    
        ]   
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    else:
        return f'Error {response.status_code}: {response.text}'


@bot.message_handler(commands=['start'])
def start(message):
    text = (
        f'Hello <b>{message.chat.username}!</b>\n'
        "I'm your personal <b>AI Assistant!</b>\n"
    )
    bot.send_message(message.chat.id, text)
    
    
@bot.message_handler(commands=['help'])
def helper(message):
    text = ('Helper Command!!')
    bot.send_message(message.chat.id, text)
    

@bot.message_handler(commands=['mode'])
def set_mode(message):
    available = "\n".join([f"• {v['name']} — {k}" for k, v in MODES.items()])
    parts = message.text.split(maxsplit=1)
    mode_key = ''
    
    if len(parts) < 2:
        mode_key = parts[1].lower().strip()
        bot.send_message(message.chat.id,f"Please choose a mode:\n{available}\n\nUsage: /mode friend",parse_mode='HTML')
        if MODES.get(mode_key):
            user_modes[message.chat.id] = mode_key  # save user mode
            bot.send_message(message.chat.id,f"✅ Mode <b>{MODES[mode_key]['name']}</b> set successfully!",parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, '❌ Invalid mode. Use /mode to see all options.')
    else:
        bot.send_message(f"Please choose a mode:\n{available}\n\nUsage: /mode friend",parse_mode='HTML')
        
@bot.message_handler(func=lambda m: True)
def text_handler(m):
    mode_key = user_modes.get(m.chat.id)
    response = fetch_answer(m.text, mode_key=mode_key)
    bot.send_message(m.chat.id, response)


if __name__ == '__main__':
    print('OpenRouter Telegram Bot is Running....')
    bot.infinity_polling()
