import requests as req
import asyncio
import time

class TeleBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = None
        self.reminders = []

    def getUpdates(self):
        payload = {"offset": self.offset, "timeout": 30}
        return req.get(f"{self.base_url}/getUpdates", params=payload).json()

    def sendMessage(self, text, cid):
        payload = {"chat_id": cid, "text": text}
        return req.post(f"{self.base_url}/sendMessage", data=payload).json()

    def sendSticker(self, cid, sticker_id):
        payload = {"chat_id": cid, "sticker": sticker_id}
        return req.post(f"{self.base_url}/sendSticker", data=payload).json()

    def sendPhoto(self, cid, url):
        payload = {"chat_id": cid, "photo": url}
        return req.post(f"{self.base_url}/sendPhoto", data=payload).json()

    # ----------------- API HELPERS -----------------
    def get_movie(self, name):
        url = f"http://www.omdbapi.com/?apikey=27ec289b&t={name}"
        return req.get(url).json()

    def get_weather(self, city):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=bf81ab202a06c347cd9c42cc6a5d3c5f&units=metric"
        return req.get(url).json()

    def get_news(self):
        url = "https://newsapi.org/v2/top-headlines?country=us&apiKey=59f47ed5549144249cd435bbf6b80bee"
        return req.get(url).json()

    def get_waifu(self, tag="maid"):
        url = f"https://api.waifu.im/search?included_tags={tag}"
        res = req.get(url).json()
        return res["images"][0]["url"]

    def get_pickup(self):
        return req.get("https://rizzapi.vercel.app/random").json()["text"]

    def get_dog(self):
        return req.get("https://dog.ceo/api/breeds/image/random").json()["message"]

    def get_cat(self):
        return req.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]

    def get_joke(self):
        res = req.get("https://v2.jokeapi.dev/joke/Any").json()
        if res["type"] == "single":
            return res["joke"]
        return f"{res['setup']}\n{res['delivery']}"

    # ----------------- MESSAGE HANDLER -----------------
    def messageHandler(self, text, cid):
        if text.startswith("/movie"):
            movie = text.split(" ", 1)[1] if " " in text else "Inception"
            data = self.get_movie(movie)
            return self.sendMessage(f"🎬 {data.get('Title')} ({data.get('Year')})\n{data.get('Plot')}", cid)

        if text.startswith("/weather"):
            city = text.split(" ", 1)[1] if " " in text else "London"
            data = self.get_weather(city)
            return self.sendMessage(f"🌤 {city}: {data['main']['temp']}°C, {data['weather'][0]['description']}", cid)

        if text == "/news":
            articles = self.get_news()["articles"][:3]
            msg = "\n\n".join([f"📰 {a['title']}\n{a['url']}" for a in articles])
            return self.sendMessage(msg, cid)

        if text.startswith("/waifu"):
            tag = text.split(" ", 1)[1] if " " in text else "maid"
            url = self.get_waifu(tag)
            return self.sendPhoto(cid, url)

        if text == "/pickup":
            return self.sendMessage(self.get_pickup(), cid)

        if text == "/dog":
            return self.sendPhoto(cid, self.get_dog())

        if text == "/cat":
            return self.sendPhoto(cid, self.get_cat())

        if text == "/joke":
            return self.sendMessage(self.get_joke(), cid)

        if text.startswith("/remindme"):
            try:
                parts = text.split(" ", 2)
                seconds = int(parts[1])
                msg = parts[2]
                self.reminders.append((time.time() + seconds, cid, msg))
                return self.sendMessage(f"⏰ Reminder set in {seconds} sec: {msg}", cid)
            except:
                return self.sendMessage("❌ Usage: /remindme 10 Take a break", cid)

        if text == "/start":
            return self.sendMessage("Welcome! 🎉\nTry: /movie /weather /news /waifu /pickup /dog /cat /joke /remindme", cid)

    # ----------------- REMINDER CHECK -----------------
    async def reminder_loop(self):
        while True:
            now = time.time()
            for r in self.reminders[:]:
                if now >= r[0]:
                    self.sendMessage(f"🔔 Reminder: {r[2]}", r[1])
                    self.reminders.remove(r)
            await asyncio.sleep(2)

    # ----------------- RUN BOT -----------------
    async def run(self):
        print("Bot is running...")
        asyncio.create_task(self.reminder_loop())
        while True:
            updates = self.getUpdates()
            if updates["result"]:
                for update in updates["result"]:
                    self.offset = update["update_id"] + 1
                    cid = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")
                    print(update)
                    self.messageHandler(text, cid)

# ----------------- START BOT -----------------
if __name__ == "__main__":
    token = "8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0"
    bot = TeleBot(token)

    asyncio.run(bot.run())