import requests as req
import time

class TeleBot:
    def __init__(self, token, sports_api_key):
        self.token = token
        self.sports_api_key = sports_api_key

    def __str__(self):
        return f"Bot with token {self.token} added successfully."

    # Telegram API wrappers
    def getUpdates(self, offset=None):
        payload = {"offset": offset, "timeout": 30}
        return req.get(f"{self.token}/getUpdates", params=payload).json()

    def sendMessage(self, text, cid):
        payload = {"text": text, "chat_id": cid}
        return req.get(f"{self.token}/sendMessage", params=payload).json()

    # ---------------- SPORTS API ---------------- #
    def getLiveScores(self):
        url = f"https://allsportsapi.com/api/football/?met=Livescore&APIkey={self.sports_api_key}"
        res = req.get(url).json()
        if "result" not in res or not res["result"]:
            return "No live matches right now ⚽"
        msg = "🔥 Live Matches:\n\n"
        for match in res["result"][:5]:  # limit to 5
            home = match["event_home_team"]
            away = match["event_away_team"]
            score = match["event_final_result"]
            time_ = match["event_status"]
            msg += f"{home} vs {away}\nScore: {score} ⏱ {time_}\n\n"
        return msg

    def getFixtures(self, league_id=152):  # 152 = Premier League as example
        url = f"https://allsportsapi.com/api/football/?met=Fixtures&leagueId={league_id}&APIkey={self.sports_api_key}"
        res = req.get(url).json()
        if "result" not in res or not res["result"]:
            return "No upcoming fixtures found ⚽"
        msg = "📅 Upcoming Fixtures:\n\n"
        for match in res["result"][:5]:
            home = match["event_home_team"]
            away = match["event_away_team"]
            date = match["event_date"]
            time_ = match["event_time"]
            msg += f"{date} {time_} → {home} vs {away}\n"
        return msg

    def getStandings(self, league_id=152):
        url = f"https://allsportsapi.com/api/football/?met=Standings&leagueId={league_id}&APIkey={self.sports_api_key}"
        res = req.get(url).json()
        if "result" not in res or not res["result"]:
            return "Standings not available 🏆"
        msg = "🏆 League Standings:\n\n"
        for team in res["result"][0]["standing"][:10]:  # top 10
            pos = team["standing_place"]
            name = team["standing_team"]
            pts = team["standing_PTS"]
            msg += f"{pos}. {name} - {pts} pts\n"
        return msg

    def getTeam(self, team_id):
        url = f"https://allsportsapi.com/api/football/?met=Teams&teamId={team_id}&APIkey={self.sports_api_key}"
        res = req.get(url).json()
        if "result" not in res or not res["result"]:
            return "Team info not found ❌"
        t = res["result"][0]
        msg = f"⚽ {t['team_name']}\nFounded: {t.get('team_founded','N/A')}\nCountry: {t.get('team_country','N/A')}\nStadium: {t.get('team_stadium','N/A')}"
        return msg

    # ---------------- MESSAGE HANDLER ---------------- #
    def messageHandler(self, text, cid):
        # Sports
        if text == "/sports":
            return self.sendMessage("⚽ Sports Menu:\n/live → Live scores\n/fixtures → Upcoming matches\n/table → League standings\n/team <id> → Team info", cid)

        if text == "/live":
            return self.sendMessage(self.getLiveScores(), cid)

        if text.startswith("/fixtures"):
            return self.sendMessage(self.getFixtures(), cid)

        if text.startswith("/table"):
            return self.sendMessage(self.getStandings(), cid)

        if text.startswith("/team"):
            parts = text.split()
            if len(parts) == 2:
                team_id = parts[1]
                return self.sendMessage(self.getTeam(team_id), cid)
            else:
                return self.sendMessage("Usage: /team <team_id>", cid)

        # Default
        if text == "/start":
            return self.sendMessage("Welcome to Coding Wizard Bot 🧙\nUse /sports for sports features ⚽", cid)

    # ---------------- BOT RUN LOOP ---------------- #
    def run(self):
        offset = None
        print("Bot is running....")
        while True:
            updates = self.getUpdates(offset)
            if updates["result"]:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    cid = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "")
                    print(update)
                    self.messageHandler(text, cid)
            time.sleep(1)


# ---------------- RUN BOT ---------------- #
BOT_TOKEN = "https://api.telegram.org/bot8016088849:AAG_kMh8ioaMHe6_Fq12hixbwRYF5hX-8I0"
SPORTS_API_KEY = "056177defc050fffd51f8915cc54f44747b5eae157cb3f497aadf3d34e595f43"

bot = TeleBot(BOT_TOKEN, SPORTS_API_KEY)
bot.run()