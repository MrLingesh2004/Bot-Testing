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

    def sendMessage(self, text, cid):
        payload = {"chat_id": cid, "text": text}
        return req.post(f"{self.base_url}/sendMessage", data=payload).json()

    def sendPhoto(self, cid, url):
        payload = {"chat_id": cid, "photo": url}
        return req.post(f"{self.base_url}/sendPhoto", data=payload).json()

    # ----------------- APIs -----------------
    def get_movie(self, name):
        return req.get(f"http://www.omdbapi.com/?apikey=27ec289b&t={name}").json()

    def get_weather(self, city):
        return req.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=bf81ab202a06c347cd9c42cc6a5d3c5f&units=metric").json()

    def get_news(self):
        return req.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=59f47ed5549144249cd435bbf6b80bee").json()

    def get_waifu(self, tag="maid"):
        return req.get(f"https://api.waifu.im/search?included_tags={tag}").json()["images"][0]["url"]

    def get_pickup(self):
        return req.get("https://rizzapi.vercel.app/random").json()["text"]

    def get_pickup2(self):
        return req.get("https://vinuxd.vercel.app/api/pickup").json()["pickup"]

    def get_dog(self):
        return req.get("https://dog.ceo/api/breeds/image/random").json()["message"]

    def get_cat(self):
        return req.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]

    def get_joke(self):
        res = req.get("https://v2.jokeapi.dev/joke/Any").json()
        if res["type"] == "single":
            return res["joke"]
        return f"{res['setup']}\n{res['delivery']}"

    def get_bored(self):
        return req.get("https://bored-api.appbrewery.com/random").json()["activity"]

    def get_meal(self, name="Arrabiata"):
        return req.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={name}").json()["meals"][0]

    def get_cocktail(self, name="margarita"):
        return req.get(f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}").json()["drinks"][0]

    def get_poem(self, author="Shakespeare"):
        return req.get(f"https://poetrydb.org/author/{author}").json()[0]["title"]

    def get_art(self):
        return req.get("https://api.artic.edu/api/v1/artworks").json()["data"][0]["title"]

    def get_country(self, name="india"):
        return req.get(f"https://restcountries.com/v3.1/name/{name}").json()[0]

    def get_pokemon(self, pid=1):
        return req.get(f"https://pokeapi.co/api/v2/pokemon/{pid}").json()

    def get_dictionary(self, word="hello"):
        return req.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}").json()[0]

    def get_qr(self, text="HelloWorld"):
        return f"https://quickchart.io/qr?text={text}"

    def get_nasa_apod(self):
        return req.get("https://api.nasa.gov/planetary/apod?api_key=7IWO5Uciaajgu0E7yVMgzDSqLt2HFHVb8Q32eSYx").json()

    def get_worldbank(self, country="IN"):
        return req.get(f"https://api.worldbank.org/v2/country/{country}?format=json").json()[1][0]

    def get_marvel(self, character="iron man"):
        public = "fc018336a9bc8036a0037f19a1fdca5c"
        private = "5f1bbba635c50ff1d57977311db1536e38482b30"
        ts = "1"
        hash_md5 = hashlib.md5((ts + private + public).encode()).hexdigest()
        url = f"http://gateway.marvel.com/v1/public/characters?name={character}&ts={ts}&apikey={public}&hash={hash_md5}"
        return req.get(url).json()["data"]["results"][0]

    # ----------------- MESSAGE HANDLER -----------------
    def messageHandler(self, text, cid):
        if text.startswith("/movie"):
            name = text.split(" ", 1)[1] if " " in text else "Inception"
            d = self.get_movie(name)
            return self.sendMessage(f"🎬 {d.get('Title')} ({d.get('Year')})\n{d.get('Plot')}", cid)

        if text.startswith("/weather"):
            city = text.split(" ", 1)[1] if " " in text else "London"
            d = self.get_weather(city)
            return self.sendMessage(f"🌤 {city}: {d['main']['temp']}°C, {d['weather'][0]['description']}", cid)

        if text == "/news":
            arts = self.get_news()["articles"][:3]
            msg = "\n\n".join([f"📰 {a['title']}\n{a['url']}" for a in arts])
            return self.sendMessage(msg, cid)

        if text.startswith("/waifu"):
            tag = text.split(" ", 1)[1] if " " in text else "maid"
            return self.sendPhoto(cid, self.get_waifu(tag))

        if text == "/pickup":
            return self.sendMessage(self.get_pickup(), cid)

        if text == "/pickup2":
            return self.sendMessage(self.get_pickup2(), cid)

        if text == "/dog":
            return self.sendPhoto(cid, self.get_dog())

        if text == "/cat":
            return self.sendPhoto(cid, self.get_cat())

        if text == "/joke":
            return self.sendMessage(self.get_joke(), cid)

        if text == "/bored":
            return self.sendMessage(self.get_bored(), cid)

        if text.startswith("/meal"):
            meal = self.get_meal()
            return self.sendMessage(f"🍽 {meal['strMeal']}\n{meal['strInstructions']}", cid)

        if text.startswith("/cocktail"):
            drink = self.get_cocktail()
            return self.sendMessage(f"🍹 {drink['strDrink']}\n{drink['strInstructions']}", cid)

        if text.startswith("/poem"):
            return self.sendMessage(f"📜 Poem: {self.get_poem()}", cid)

        if text.startswith("/art"):
            return self.sendMessage(f"🎨 Artwork: {self.get_art()}", cid)

        if text.startswith("/country"):
            name = text.split(" ", 1)[1] if " " in text else "India"
            c = self.get_country(name)
            return self.sendMessage(f"🌍 {c['name']['common']} - Capital: {c['capital'][0]}", cid)

        if text.startswith("/pokemon"):
            pid = text.split(" ", 1)[1] if " " in text else "1"
            p = self.get_pokemon(pid)
            return self.sendMessage(f"⚡ {p['name'].title()} - Base XP: {p['base_experience']}", cid)

        if text.startswith("/dict"):
            word = text.split(" ", 1)[1] if " " in text else "hello"
            d = self.get_dictionary(word)
            return self.sendMessage(f"📖 {word}: {d['meanings'][0]['definitions'][0]['definition']}", cid)

        if text.startswith("/qr"):
            txt = text.split(" ", 1)[1] if " " in text else "HelloWorld"
            return self.sendPhoto(cid, self.get_qr(txt))

        if text == "/nasa":
            d = self.get_nasa_apod()
            self.sendPhoto(cid, d["url"])
            return self.sendMessage(f"🌌 {d['title']}\n{d['explanation']}", cid)

        if text.startswith("/worldbank"):
            code = text.split(" ", 1)[1] if " " in text else "IN"
            d = self.get_worldbank(code)
            return self.sendMessage(f"🏦 {d['name']} ({d['region']['value']})", cid)

        if text.startswith("/marvel"):
            name = text.split(" ", 1)[1] if " " in text else "Iron Man"
            d = self.get_marvel(name)
            return self.sendMessage(f"🦸 {d['name']}\n{d['description']}", cid)

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
            return self.sendMessage(
                "Welcome! 🎉\n"
                "Try: /movie /weather /news /waifu /pickup /dog /cat /joke /bored /meal /cocktail /poem "
                "/art /country /pokemon /dict /qr /nasa /worldbank /marvel /remindme",
                cid
            )

    # ----------------- REMINDERS -----------------
    async def reminder_loop(self):
        while True:
            now = time.time()
            for r in self.reminders[:]:
                if now >= r[0]:
                    self.sendMessage(f"🔔 Reminder: {r[2]}", r[1])
                    self.reminders.remove(r)
            await asyncio.sleep(2)

    # ----------------- RUN -----------------
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