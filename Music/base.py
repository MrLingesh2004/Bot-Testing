import json, os, yt_dlp, re
from datetime import datetime, timedelta

class UserHandler:
    def __init__(self, file_path="users.json"):
        self.file_path = file_path
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f, indent=4)

    def read_all(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_all(self, data):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def read_file(self, user_id):
        return self.read_all().get(str(user_id))

    def save_file(self, user_id, user_data):
        data = self.read_all()
        data[str(user_id)] = user_data
        self.write_all(data)

    def fetch_user(self, user_id, username=None):
        data = self.read_all()
        user_id = str(user_id)
        if user_id not in data:
            data[user_id] = {
                "username": username or f"user{user_id}",
                "user_id": user_id,
                "downloads": 0,
                "playlists": [],
                "premium": False,
                "premium_expiry": None,
                "created_at": datetime.now().isoformat()
            }
            self.write_all(data)
        return data[user_id]

    def add_to_playlist(self, user_id, playlist_name):
        user = self.fetch_user(user_id)
        if playlist_name in user["playlists"]:
            user["playlists"].remove(playlist_name)
        user["playlists"].insert(0, playlist_name)
        if len(user["playlists"]) > 20:
            user["playlists"] = user["playlists"][:20]
        self.save_file(user_id, user)
        return user

    def set_premium(self, target_id, days=30):
        user = self.fetch_user(target_id)
        user["premium"] = True
        expiry = datetime.now() + timedelta(days=days)
        user["premium_expiry"] = expiry.isoformat()
        self.save_file(target_id, user)
        return user

    def revoke_premium(self, target_id):
        user = self.fetch_user(target_id)
        user["premium"] = False
        user["premium_expiry"] = None
        self.save_file(target_id, user)
        return user

    def extend_premium(self, target_id, days=30):
        user = self.fetch_user(target_id)
        expiry = datetime.fromisoformat(user["premium_expiry"]) + timedelta(days=days) if user["premium_expiry"] else datetime.now() + timedelta(days=days)
        user["premium"] = True
        user["premium_expiry"] = expiry.isoformat()
        self.save_file(target_id, user)
        return user


class AdminHandler(UserHandler):
    def __init__(self):
        self.path = 'users.json'
        self.admin = [8322030170]

    def check(self, admin_id):
        return str(admin_id) in [str(a) for a in self.admin]

    def grant(self, admin_id, user_id, month=1):
        if not self.check(admin_id):
            return "🚫 You don't have permission to perform this action."
        self.set_premium(user_id, days=month * 30)
        return f"✅ Premium granted for {month} month(s) to user {user_id}."

    def revoke(self, admin_id, user_id):
        if not self.check(admin_id):
            return "🚫 You don't have permission to perform this action."
        self.revoke_premium(user_id)
        return f"❎ Premium revoked for user {user_id}."

    def extend(self, admin_id, user_id, month=1):
        if not self.check(admin_id):
            return "🚫 You don't have permission to perform this action."
        self.extend_premium(user_id, days=month * 30)
        return f"⏫ Extended premium for {month} month(s) for user {user_id}."

    def broadcast(self, admin_id, message, send_func):
        if not self.check(admin_id):
            return "🚫 You don't have permission to perform this action."
        all_users = self.read_all()
        count = 0
        for user_id in all_users:
            try:
                send_func(int(user_id), message)
                count += 1
            except Exception:
                continue
        return f"📢 Broadcast sent to {count} users!"
        
        
class YoutubeHandler:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)

    # ----------------- SEARCH -----------------
    def search_song(self, query, limit=5):
        """
        Search YouTube for a song.
        Returns a list of dicts: [{'title': ..., 'webpage_url': ..., 'id': ...}, ...]
        """
        try:
            ydl_opts = {"quiet": True, "format": "bestaudio/best"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            
            entries = search_result.get("entries", [])
            results = []
            for e in entries:
                results.append({
                    "title": e.get("title"),
                    "webpage_url": e.get("webpage_url"),
                    "id": e.get("id")
                })
            return results
        except Exception as e:
            print(f"Search failed: {str(e)}")
            return []

    # ----------------- DOWNLOAD -----------------
    def download_song(self, url, title=None):
        """
        Download a song from YouTube as MP3.
        Returns dict with {'title': ..., 'file_path': ...}
        """
        try:
            # Convert mobile URL to standard desktop URL
            url = url.replace("m.youtube.com", "www.youtube.com")

            # If title not given, fetch it
            if not title:
                info = yt_dlp.YoutubeDL({"quiet": True}).extract_info(url, download=False)
                title = info.get("title", "song")

            # Sanitize filename
            safe_title = re.sub(r'[^a-zA-Z0-9]+', '_', title)
            file_path = os.path.join(self.download_path, f"{safe_title}.mp3")

            # Download options
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": file_path,
                "quiet": True,
                "noplaylist": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }],
                "ignoreerrors": True,
                "noprogress": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            return {"title": title, "file_path": file_path}

        except Exception as e:
            print(f"Download failed: {str(e)}")
            return {"title": title, "file_path": None, "error": str(e)}