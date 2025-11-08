import requests, json

user_modes = {}
f = open('modes.json', 'r')
MODES = json.load(f)

class TelegramBot:
    def __init__(self, Token, API):
        self.url = f'https://api.telegram.org/bot{Token}'
        self.api = API
        
    def get_response(self, text, model='gpt-3.5-turbo', mode_key=None):
        mode = MODES.get(mode_key, {})
        url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api}',
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
        
    def get_updates(self, offset=None, timeout=30):
        params = { 'offset': offset, 'timeout': timeout }
        return requests.get(f'{self.url}/getUpdates', params=params).json()
        
    def fetch_data(self, updates):
        if updates['result']:
            for update in updates['result']:
                offset, cid, text = update['update_id'] + 1, update['message']['chat']['id'], update['message']['text']
                return offset, cid, text
                
    def message_handler(self, cid, text):
        if text and text == '/start':
            response = (
                'Hello User!\n'
                "I'm your personal AI Assistant!\n"
            )
            self.send_message(cid, response)
            return True, text
            
        elif text and text == '/help':
            response = 'Helper Command!!'
            self.send_message(cid, response)
            return True, text
            
        elif text and text.startswith('/mode'):
            available = "\n".join([f"• {v['name']} — {k}" for k, v in MODES.items()])
            parts = text.split(maxsplit=1)
            mode_key = ''
            
            if len(parts) == 2:
                mode_key = parts[1].lower().strip()
                self.send_message(cid, f"Please choose a mode:\n{available}\n\nUsage: /mode friend")
                if MODES.get(mode_key):
                    user_modes[cid] = mode_key  # save user mode
                    self.send_message(cid, f"✅ Mode {MODES[mode_key]['name']} set successfully!")
                    return True, text
                else:
                    self.send_message(cid, '❌ Invalid mode. Use /mode to see all options.')
                    return True, text
                    
            else:
                self.send_message(f"Please choose a mode:\n{available}\n\nUsage: /mode friend")
                return True, text
            
            
        elif text and not text.startswith('/'):
            if text.lower() == 'bye':
                self.send_message(cid, text)
                return True, text
            else:    
                mode_key = user_modes.get(cid)
                response = self.get_response(text, mode_key=mode_key)
                self.send_message(cid, response)
                return True, text
        
    def send_message(self, cid, text):
        payload = { 'chat_id': cid, 'text': text }
        return requests.post(f'{self.url}/sendMessage', data=payload).json()
        
    def request(self):
        offset=None
        is_run = True
        print('OpenRouter Telegram Bot is Running....')
        while is_run:
            updates = self.get_updates(offset)
            offset, cid, text = self.fetch_data(updates)
            is_run, response = self.message_handler(cid, text)
            print(is_run, updates)
            
API_KEY = ''
Token = ''

bot = TelegramBot(Token, API_KEY)
bot.request()
