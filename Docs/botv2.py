import requests as req
import asyncio
import time
import hashlib

class TeleBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = None
        self.reminders = []

    # ----------------- TELEGRAM -----------------
    def getUpdates(self):
        payload = {"offset": self.offset, "timeout": 30}
        return req.get(f"{self.base_url}/getUpdates", params=payload).json()

    def sendMessage(self, text, cid, keyboard=None):
        payload = {"chat_id": cid, "text": text}
        if keyboard:
            payload["reply_markup"] = keyboard
        return req.post(f"{self.base_url}/sendMessage", json=payload).json()

    def sendPhoto(self, cid, url, caption=None, keyboard=None):
        payload = {"chat_id": cid, "photo": url}
        if caption:
            payload["caption"] = caption
        if keyboard:
            payload["reply_markup"] = keyboard
        return req.post(f"{self.base_url}/sendPhoto", json=payload).json()

    def answerCallback(self, callback_id, text="✅ Done"):
        payload = {"callback_query_id": callback_id, "text": text}
        return req.post(f"{self.base_url}/answerCallbackQuery", data=payload).json()

    # ----------------- APIs -----------------
    def get_pickup(self):
        return req.get("https://rizzapi.vercel.app/random").json()["text"]

    def get_cat(self):
        return req.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]

    def get_dog(self):
        return req.get("https://dog.ceo/api/breeds/image/random").json()["message"]

    def get_joke(self):
        res = req.get("https://v2.jokeapi.dev/joke/Any").json()
        if res["type"] == "single":
            return res["joke"]
        return f"{res['setup']}\n{res['delivery']}"

    # ----------------- KEYBOARDS -----------------
    def main_menu(self):
        return {
            "inline_keyboard": [
                [
                    {"text": "🐶 Dog", "callback_data": "dog"},
                    {"text": "🐱 Cat", "callback_data": "cat"},
                ],
                [
                    {"text": "😂 Joke", "callback_data": "joke"},
                    {"text": "💬 Pickup Line", "callback_data": "pickup"},
                ],
                [
                    {"text": "🌌 NASA APOD", "callback_data": "nasa"},
                    {"text": "📰 News", "callback_data": "news"},
                ]
            ]
        }

    # ----------------- MESSAGE HANDLER -----------------
    def messageHandler(self, text, cid):
        if text == "/start":
            return self.sendMessage("Welcome! 🎉\nChoose an option:", cid, self.main_menu())

    def callbackHandler(self, data, cid, callback_id):
        if data == "dog":
            self.answerCallback(callback_id)
            return self.sendPhoto(cid, self.get_dog(), "🐶 Here's a random dog!")
        if data == "cat":
            self.answerCallback(callback_id)
            return self.sendPhoto(cid, self.get_cat(), "🐱 Here's a random cat!")
        if data == "joke":
            self.answerCallback(callback_id)
            return self.sendMessage(f"😂 {self.get_joke()}", cid)
        if data == "pickup":
            self.answerCallback(callback_id)
            return self.sendMessage(f"💬 {self.get_pickup()}", cid)
        if data == "nasa":
            self.answerCallback(callback_id)
            d = req.get("https://api.nasa.gov/planetary/apod?api_key=7IWO5Uciaajgu0E7yVMgzDSqLt2HFHVb8Q32eSYx").json()
            return self.sendPhoto(cid, d["url"], f"🌌 {d['title']}\n{d['explanation']}")
        if data == "news":
            self.answerCallback(callback_id)
            arts = req.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=59f47ed5549144249cd435bbf6b80bee").json()["articles"][:3]
            msg = "\n\n".join([f"📰 {a['title']}\n{a['url']}" for a in arts])
            return self.sendMessage(msg, cid)

    # ----------------- RUN -----------------
    async def run(self):
        print("Bot is running with InlineKeyboard...")
        while True:
            updates = self.getUpdates()
            if updates["result"]:
                for update in updates["result"]:
                    self.offset = update["update_id"] + 1

                    if "message" in update and "text" in update["message"]:
                        cid = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        print(update)
                        self.messageHandler(text, cid)

                    if "callback_query" in update:
                        cq = update["callback_query"]
                        cid = cq["message"]["chat"]["id"]
                        data = cq["data"]
                        cb_id = cq["id"]
                        print("Callback:", data)
                        self.callbackHandler(data, cid, cb_id)


# ----------------- START BOT -----------------
if __name__ == "__main__":
    token = "8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0"
    bot = TeleBot(token)
    asyncio.run(bot.run())