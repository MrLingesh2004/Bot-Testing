import requests as req
import asyncio
import hashlib

class TeleBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = None

    # ----------------- TELEGRAM -----------------
    def getUpdates(self):
        return req.get(f"{self.base_url}/getUpdates", params={"offset": self.offset, "timeout": 30}).json()

    def sendMessage(self, text, cid, keyboard=None):
        payload = {"chat_id": cid, "text": text}
        if keyboard: payload["reply_markup"] = keyboard
        return req.post(f"{self.base_url}/sendMessage", json=payload).json()

    def sendPhoto(self, cid, url, caption=None):
        payload = {"chat_id": cid, "photo": url}
        if caption: payload["caption"] = caption
        return req.post(f"{self.base_url}/sendPhoto", data=payload).json()

    def answerCallback(self, cbid, text="✅ Done"):
        return req.post(f"{self.base_url}/answerCallbackQuery", data={"callback_query_id": cbid, "text": text}).json()

    # ----------------- API HELPERS -----------------
    def get_dog(self): return req.get("https://dog.ceo/api/breeds/image/random").json()["message"]
    def get_cat(self): return req.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]
    def get_pickup(self): return req.get("https://rizzapi.vercel.app/random").json()["text"]
    def get_pickup2(self): return req.get("https://vinuxd.vercel.app/api/pickup").json()["pickup"]
    def get_joke(self):
        j = req.get("https://v2.jokeapi.dev/joke/Any").json()
        return j["joke"] if j["type"] == "single" else f"{j['setup']}\n{j['delivery']}"
    def get_nasa(self): return req.get("https://api.nasa.gov/planetary/apod?api_key=7IWO5Uciaajgu0E7yVMgzDSqLt2HFHVb8Q32eSYx").json()
    def get_news(self): return req.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=59f47ed5549144249cd435bbf6b80bee").json()["articles"][:3]
    def get_weather(self, city="London"): return req.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=bf81ab202a06c347cd9c42cc6a5d3c5f&units=metric").json()
    def get_movie(self, name="Inception"): return req.get(f"http://www.omdbapi.com/?apikey=27ec289b&t={name}").json()
    def get_meal(self): return req.get("https://www.themealdb.com/api/json/v1/1/search.php?s=Arrabiata").json()["meals"][0]
    def get_cocktail(self): return req.get("https://www.thecocktaildb.com/api/json/v1/1/search.php?s=margarita").json()["drinks"][0]
    def get_country(self, name="india"): return req.get(f"https://restcountries.com/v3.1/name/{name}").json()[0]
    def get_pokemon(self, pid=25): return req.get(f"https://pokeapi.co/api/v2/pokemon/{pid}").json()
    def get_dict(self, word="hello"): return req.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()[0]["meanings"][0]["definitions"][0]["definition"]
    def get_poetry(self): return req.get("https://poetrydb.org/Shakespeare").json()[0]["lines"][:4]
    def get_art(self): return req.get("https://api.artic.edu/api/v1/artworks").json()["data"][0]
    def get_bored(self): return req.get("https://bored-api.appbrewery.com/random").json()["activity"]
    def get_marvel(self):
        pub, priv = "fc018336a9bc8036a0037f19a1fdca5c", "5f1bbba635c50ff1d57977311db1536e38482b30"
        ts = "1"
        h = hashlib.md5((ts + priv + pub).encode()).hexdigest()
        return req.get(f"http://gateway.marvel.com/v1/public/characters?name=Iron%20Man&ts={ts}&apikey={pub}&hash={h}").json()["data"]["results"][0]
    def get_worldbank(self): return req.get("https://api.worldbank.org/countries?format=json").json()[1][0]
    def get_qr(self, txt="Hello"): return f"https://quickchart.io/qr?text={txt}"
    def get_waifu(self): return req.get("https://api.waifu.im/search?included_tags=maid").json()["images"][0]["url"]
    def get_openlib(self): return req.get("https://openlibrary.org/search.json?q=wednesday").json()["docs"][0]

    # ----------------- MENUS -----------------
    def menu1(self):
        return {"inline_keyboard":[
            [{"text":"🐶 Dog","callback_data":"dog"},{"text":"🐱 Cat","callback_data":"cat"}],
            [{"text":"😂 Joke","callback_data":"joke"},{"text":"💬 Pickup","callback_data":"pickup"}],
            [{"text":"🌌 NASA","callback_data":"nasa"},{"text":"📰 News","callback_data":"news"}],
            [{"text":"⏭ Next","callback_data":"menu2"}]
        ]}
    def menu2(self):
        return {"inline_keyboard":[
            [{"text":"🌤 Weather","callback_data":"weather"},{"text":"🎬 Movie","callback_data":"movie"}],
            [{"text":"🍽 Meal","callback_data":"meal"},{"text":"🍹 Cocktail","callback_data":"cocktail"}],
            [{"text":"🌍 Country","callback_data":"country"},{"text":"⚡ Pokémon","callback_data":"pokemon"}],
            [{"text":"⏮ Back","callback_data":"menu1"},{"text":"⏭ Next","callback_data":"menu3"}]
        ]}
    def menu3(self):
        return {"inline_keyboard":[
            [{"text":"📚 Dictionary","callback_data":"dict"},{"text":"🖼 Art","callback_data":"art"}],
            [{"text":"📖 Poetry","callback_data":"poetry"},{"text":"💤 Bored","callback_data":"bored"}],
            [{"text":"🦸 Marvel","callback_data":"marvel"},{"text":"📊 WorldBank","callback_data":"worldbank"}],
            [{"text":"⏮ Back","callback_data":"menu2"},{"text":"⏭ Next","callback_data":"menu4"}]
        ]}
    def menu4(self):
        return {"inline_keyboard":[
            [{"text":"📸 QR","callback_data":"qr"},{"text":"🎴 Waifu","callback_data":"waifu"}],
            [{"text":"📚 OpenLib","callback_data":"openlib"},{"text":"🎶 Pickup2","callback_data":"pickup2"}],
            [{"text":"📡 AP Test","callback_data":"ap"},{"text":"🔑 GA Test","callback_data":"ga"}],
            [{"text":"⏮ Back","callback_data":"menu3"}]
        ]}

    # ----------------- HANDLERS -----------------
    def messageHandler(self, text, cid):
        if text=="/start": self.sendMessage("Welcome 🚀 Pick an option:", cid, self.menu1())

    def callbackHandler(self, data, cid, cbid):
        self.answerCallback(cbid)
        if data.startswith("menu"): return self.sendMessage("📖 Menu:", cid, getattr(self, data)())

        if data=="dog": return self.sendPhoto(cid, self.get_dog(), "🐶 Woof!")
        if data=="cat": return self.sendPhoto(cid, self.get_cat(), "🐱 Meow!")
        if data=="pickup": return self.sendMessage("💬 "+self.get_pickup(), cid)
        if data=="pickup2": return self.sendMessage("🎶 "+self.get_pickup2(), cid)
        if data=="joke": return self.sendMessage("😂 "+self.get_joke(), cid)
        if data=="nasa": d=self.get_nasa(); return self.sendPhoto(cid, d["url"], f"🌌 {d['title']}")
        if data=="news": arts=self.get_news(); return self.sendMessage("\n\n".join([a['title'] for a in arts]), cid)
        if data=="weather": w=self.get_weather(); return self.sendMessage(f"🌤 {w['name']}: {w['main']['temp']}°C", cid)
        if data=="movie": m=self.get_movie(); return self.sendMessage(f"🎬 {m['Title']} ({m['Year']})", cid)
        if data=="meal": meal=self.get_meal(); return self.sendMessage(f"🍽 {meal['strMeal']}", cid)
        if data=="cocktail": d=self.get_cocktail(); return self.sendMessage(f"🍹 {d['strDrink']}", cid)
        if data=="country": c=self.get_country(); return self.sendMessage(f"🌍 {c['name']['common']}", cid)
        if data=="pokemon": p=self.get_pokemon(); return self.sendMessage(f"⚡ {p['name']}", cid)
        if data=="dict": return self.sendMessage("📚 "+self.get_dict(), cid)
        if data=="poetry": return self.sendMessage("📖 "+"\n".join(self.get_poetry()), cid)
        if data=="art": a=self.get_art(); return self.sendMessage(f"🖼 {a['title']}", cid)
        if data=="bored": return self.sendMessage("💤 "+self.get_bored(), cid)
        if data=="marvel": m=self.get_marvel(); return self.sendMessage("🦸 "+m['name'], cid)
        if data=="worldbank": w=self.get_worldbank(); return self.sendMessage("📊 "+w['name'], cid)
        if data=="qr": return self.sendPhoto(cid, self.get_qr("Hello World"), "📸 QR Code")
        if data=="waifu": return self.sendPhoto(cid, self.get_waifu(), "🎴 Waifu ❤️")
        if data=="openlib": o=self.get_openlib(); return self.sendMessage("📚 "+o['title_suggest'], cid)
        if data=="ap": return self.sendMessage("📡 AP Test working", cid)
        if data=="ga": return self.sendMessage("🔑 GA Token Ready", cid)

    # ----------------- RUN -----------------
    async def run(self):
        print("Bot online with 4-page menu 🚀")
        while True:
            updates=self.getUpdates()
            if updates["result"]:
                for u in updates["result"]:
                    self.offset=u["update_id"]+1
                    if "message" in u and "text" in u["message"]:
                        self.messageHandler(u["message"]["text"], u["message"]["chat"]["id"])
                    if "callback_query" in u:
                        cq=u["callback_query"]
                        self.callbackHandler(cq["data"], cq["message"]["chat"]["id"], cq["id"])


# ----------------- START -----------------
if __name__=="__main__":
    token="8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0"
    bot=TeleBot(token)
    asyncio.run(bot.run())