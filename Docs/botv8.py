import requests as req
import yt_dlp
import time

class YouTubeBot:
    def __init__(self, token):
        self.token = token

    # Telegram Helpers
    def sendMessage(self, text, cid):
        payload = {"chat_id": cid, "text": text}
        return req.post(f"{self.token}/sendMessage", data=payload).json()

    def sendPhoto(self, photo_url, cid, caption=""):
        payload = {"chat_id": cid, "photo": photo_url, "caption": caption}
        return req.post(f"{self.token}/sendPhoto", data=payload).json()

    def sendAudio(self, audio_url, cid, title=""):
        payload = {"chat_id": cid, "audio": audio_url, "title": title}
        return req.post(f"{self.token}/sendAudio", data=payload).json()

    # Telegram Updates
    def getUpdates(self, offset=None):
        payload = {"offset": offset, "timeout": 30}
        return req.get(f"{self.token}/getUpdates", params=payload).json()

    # ------------------------
    # YT-dlp Functions
    def ytSearch(self, query, max_results=3):
        ydl_opts = {"format": "bestaudio/best", "noplaylist": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)['entries']
            videos = []
            for v in results:
                videos.append({
                    "title": v["title"],
                    "url": v["webpage_url"],
                    "audio": v["url"],
                    "thumbnail": v["thumbnail"]
                })
            return videos

    def ytPlaylist(self, url):
        ydl_opts = {"format": "bestaudio/best", "noplaylist": False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            videos = []
            for v in info["entries"]:
                videos.append({
                    "title": v["title"],
                    "url": v["webpage_url"],
                    "audio": v["url"],
                    "thumbnail": v["thumbnail"]
                })
            return videos

    def ytDownload(self, url):
        ydl_opts = {"format": "bestaudio/best"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info["title"],
                "audio": info["url"],
                "thumbnail": info.get("thumbnail")
            }

    # ------------------------
    # Bot Message Handler
    def handleMessage(self, text, cid):
        if text.startswith("/search"):
            query = text.split(maxsplit=1)[1]
            videos = self.ytSearch(query)
            for v in videos:
                self.sendPhoto(v["thumbnail"], cid, caption=f"🎥 {v['title']}\n{v['url']}")
            return

        if text.startswith("/playlist"):
            url = text.split(maxsplit=1)[1]
            videos = self.ytPlaylist(url)
            msg = f"Playlist has {len(videos)} videos:\n\n"
            for v in videos[:10]:
                msg += f"{v['title']}\n{v['url']}\n\n"
            return self.sendMessage(msg, cid)

        if text.startswith("/download"):
            url = text.split(maxsplit=1)[1]
            song = self.ytDownload(url)
            if song.get("thumbnail"):
                self.sendPhoto(song["thumbnail"], cid, caption=f"🎵 {song['title']}")
            return self.sendAudio(song["audio"], cid, title=song["title"])

        if text.startswith("/help"):
            help_text = (
                "/search <query> → Search YouTube videos\n"
                "/playlist <URL> → Get playlist info\n"
                "/download <URL> → Download audio (YT-dlp)\n"
            )
            return self.sendMessage(help_text, cid)

    # ------------------------
    # Run Bot
    def run(self):
        offset = None
        print("YouTubeBot running...")
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
            time.sleep(1)

# ------------------------
# Initialize Bot
bot = YouTubeBot("https://api.telegram.org/bot8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0")
bot.run()