import requests as req

class TeleBot:
    def __init__(self, token):
        self.token = token

    def sendMessage(self, text, cid):
        payload = {"chat_id": cid, "text": text}
        return req.post(f"{self.token}/sendMessage", data=payload).json()

    def sendPhoto(self, photo_url, cid, caption=""):
        payload = {"chat_id": cid, "photo": photo_url, "caption": caption}
        return req.post(f"{self.token}/sendPhoto", data=payload).json()

    def getUpdates(self, offset=None):
        payload = {"offset": offset, "timeout": 30}
        return req.get(f"{self.token}/getUpdates", params=payload).json()

    # ✅ New function: Random User
    def randomUser(self):
        res = req.get("https://randomuser.me/api/").json()
        user = res["results"][0]
        name = f"{user['name']['first']} {user['name']['last']}"
        email = user["email"]
        phone = user["phone"]
        country = user["location"]["country"]
        photo = user["picture"]["large"]
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "country": country,
            "photo": photo
        }

    def handleMessage(self, text, cid):
        if text.startswith("/user"):
            user = self.randomUser()
            caption = (
                f"👤 *{user['name']}*\n"
                f"📧 {user['email']}\n"
                f"📞 {user['phone']}\n"
                f"🌍 {user['country']}"
            )
            return self.sendPhoto(user["photo"], cid, caption=caption)

        if text.startswith("/help"):
            return self.sendMessage("/user → Get a random user profile", cid)

    def run(self):
        offset = None
        print("Bot is running...")
        while True:
            updates = self.getUpdates(offset)
            if updates["result"]:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    message = update["message"]
                    cid = message["chat"]["id"]
                    text = message.get("text", "")
                    print(f"Received: {text}")
                    self.handleMessage(text, cid)

# Run bot
bot = TeleBot("https://api.telegram.org/bot8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0")
bot.run()