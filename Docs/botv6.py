import requests as req
import asyncio
import hashlib

class TeleBot:
    def __init__(self, token, or_key=None):
        self.token = token
        self.or_key = or_key
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

    # ----------------- OPENROUTER -----------------
    def ask_ai(self, query):
        headers = {
            "Authorization": f"Bearer {self.or_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "openrouter/auto",  # auto-picks best available
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant inside Telegram."},
                {"role": "user", "content": query}
            ]
        }
        r = req.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"⚠️ OpenRouter error: {r.text}"

    # ----------------- MENUS -----------------
    def menu4(self):
        return {"inline_keyboard":[
            [{"text":"📸 QR","callback_data":"qr"},{"text":"🎴 Waifu","callback_data":"waifu"}],
            [{"text":"📚 OpenLib","callback_data":"openlib"},{"text":"🎶 Pickup2","callback_data":"pickup2"}],
            [{"text":"🧠 AI Chat","callback_data":"ai"},{"text":"📊 AP Test","callback_data":"ap"}],
            [{"text":"⏮ Back","callback_data":"menu3"}]
        ]}

    # ----------------- HANDLERS -----------------
    def messageHandler(self, text, cid):
        if text=="/start":
            from_page1 = {"inline_keyboard":[
                [{"text":"🐶 Dog","callback_data":"dog"},{"text":"🐱 Cat","callback_data":"cat"}],
                [{"text":"😂 Joke","callback_data":"joke"},{"text":"💬 Pickup","callback_data":"pickup"}],
                [{"text":"🌌 NASA","callback_data":"nasa"},{"text":"📰 News","callback_data":"news"}],
                [{"text":"⏭ Next","callback_data":"menu2"}]
            ]}
            self.sendMessage("Welcome 🚀 Pick an option:", cid, from_page1)

        if text.startswith("/ask"):
            q = text.replace("/ask", "").strip()
            if not q:
                return self.sendMessage("❓ Usage: `/ask your question`", cid)
            ans = self.ask_ai(q)
            return self.sendMessage("🧠 " + ans, cid)

    def callbackHandler(self, data, cid, cbid):
        self.answerCallback(cbid)

        if data=="ai":
            return self.sendMessage("🧠 Send me your question using /ask <your text>", cid)

        # (keep the other handlers for dog, cat, joke, nasa, etc. from before...)

    # ----------------- RUN -----------------
    async def run(self):
        print("Bot online with OpenRouter integration 🚀")
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
    or_key="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"
    bot=TeleBot(token, or_key)
    asyncio.run(bot.run())