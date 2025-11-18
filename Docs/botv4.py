import requests as req
import asyncio
import time
import hashlib

class TeleBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = None

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

    # ----------------- API HELPERS -----------------
    def get_dog(self): return req.get("https://dog.ceo/api/breeds/image/random").json()["message"]
    def get_cat(self): return req.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]
    def get_pickup(self): return req.get("https://rizzapi.vercel.app/random").json()["text"]
    def get_joke(self):
        res = req.get("https://v2.jokeapi.dev/joke/Any").json()
        return res["joke"] if res["type"] == "single" else f"{res['setup']}\n{res['delivery']}"
    def get_nasa(self): return req.get("https://api.nasa.gov/planetary/apod?api_key=7IWO5Uciaajgu0E7yVMgzDSqLt2HFHVb8Q32eSYx").json()
    def get_news(self): return req.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=59f47ed5549144249cd435bbf6b80bee").json()["articles"][:3]
    def get_weather(self, city="London"): return req.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=bf81ab202a06c347cd9c42cc6a5d3c5f&units=metric").json()
    def get_movie(self, name="Inception"): return req.get(f"http://www.omdbapi.com/?apikey=27ec289b&t={name}").json()
    def get_meal(self, name="Arrabiata"): return req.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={name}").json()["meals"][0]
    def get_cocktail(self, name="margarita"): return req.get(f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}").json()["drinks"][0]
    def get_country(self, name="india"): return req.get(f"https://restcountries.com/v3.1/name/{name}").json()[0]
    def get_pokemon(self, pid=1): return req.get(f"https://pokeapi.co/api/v2/pokemon/{pid}").json()

    # ----------------- KEYBOARDS -----------------
    def menu_page1(self):
        return {
            "inline_keyboard": [
                [{"text": "🐶 Dog", "callback_data": "dog"},
                 {"text": "🐱 Cat", "callback_data": "cat"}],
                [{"text": "😂 Joke", "callback_data": "joke"},
                 {"text": "💬 Pickup", "callback_data": "pickup"}],
                [{"text": "🌌 NASA", "callback_data": "nasa"},
                 {"text": "📰 News", "callback_data": "news"}],
                [{"text": "⏭ Next", "callback_data": "menu2"}]
            ]
        }

    def menu_page2(self):
        return {
            "inline_keyboard": [
                [{"text": "🌤 Weather", "callback_data": "weather"},
                 {"text": "🎬 Movie", "callback_data": "movie"}],
                [{"text": "🍽 Meal", "callback_data": "meal"},
                 {"text": "🍹 Cocktail", "callback_data": "cocktail"}],
                [{"text": "🌍 Country", "callback_data": "country"},
                 {"text": "⚡ Pokemon", "callback_data": "pokemon"}],
                [{"text": "⏮ Back", "callback_data": "menu1"}]
            ]
        }

    # ----------------- MESSAGE HANDLER -----------------
    def messageHandler(self, text, cid):
        if text == "/start":
            return self.sendMessage("Welcome! 🎉\nChoose an option:", cid, self.menu_page1())

    def callbackHandler(self, data, cid, callback_id):
        self.answerCallback(callback_id)

        if data == "menu1":
            return self.sendMessage("📖 Page 1:", cid, self.menu_page1())
        if data == "menu2":
            return self.sendMessage("📖 Page 2:", cid, self.menu_page2())

        if data == "dog": return self.sendPhoto(cid, self.get_dog(), "🐶 Here's a dog!")
        if data == "cat": return self.sendPhoto(cid, self.get_cat(), "🐱 Here's a cat!")
        if data == "pickup": return self.sendMessage(f"💬 {self.get_pickup()}", cid)
        if data == "joke": return self.sendMessage(f"😂 {self.get_joke()}", cid)

        if data == "nasa":
            d = self.get_nasa()
            return self.sendPhoto(cid, d["url"], f"🌌 {d['title']}\n{d['explanation']}")
        if data == "news":
            arts = self.get_news()
            msg = "\n\n".join([f"📰 {a['title']}\n{a['url']}" for a in arts])
            return self.sendMessage(msg, cid)

        if data == "weather":
            w = self.get_weather("London")
            return self.sendMessage(f"🌤 London: {w['main']['temp']}°C, {w['weather'][0]['description']}", cid)
        if data == "movie":
            m = self.get_movie("Inception")
            return self.sendMessage(f"🎬 {m['Title']} ({m['Year']})\n{m['Plot']}", cid)

        if data == "meal":
            meal = self.get_meal()
            return self.sendMessage(f"🍽 {meal['strMeal']}\n{meal['strInstructions']}", cid)
        if data == "cocktail":
            drink = self.get_cocktail()
            return self.sendMessage(f"🍹 {drink['strDrink']}\n{drink['strInstructions']}", cid)

        if data == "country":
            c = self.get_country("India")
            return self.sendMessage(f"🌍 {c['name']['common']} - Capital: {c['capital'][0]}", cid)
        if data == "pokemon":
            p = self.get_pokemon(25)
            return self.sendMessage(f"⚡ {p['name'].title()} - Base XP: {p['base_experience']}", cid)

    # ----------------- RUN -----------------
    async def run(self):
        print("Bot running with multi-page menu...")
        while True:
            updates = self.getUpdates()
            if updates["result"]:
                for update in updates["result"]:
                    self.offset = update["update_id"] + 1

                    if "message" in update and "text" in update["message"]:
                        cid = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        self.messageHandler(text, cid)

                    if "callback_query" in update:
                        cq = update["callback_query"]
                        cid = cq["message"]["chat"]["id"]
                        data = cq["data"]
                        cb_id = cq["id"]
                        self.callbackHandler(data, cid, cb_id)


# ----------------- START BOT -----------------
if __name__ == "__main__":
    token = "8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0"
    bot = TeleBot(token)
    asyncio.run(bot.run())