import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from base import UserHandler, AdminHandler, YoutubeHandler

# ================== BOT SETUP ==================
BOT_TOKEN = ''
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

handler = UserHandler('users.json')
admin = AdminHandler()
yt_handler = YoutubeHandler('downloads')  # Ensure folder exists


# ================== UTILITIES ==================
def mainMenu():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        ('👤 User Info', 'userinfo'),
        ('🎧 Playlists', 'playlists_info'),
        ('💎 Upgrade to Premium', 'premium_info'),
        ('❓ Help', 'help')
    ]
    kb.add(*[InlineKeyboardButton(text, callback_data=data) for text, data in buttons])
    return kb


def userInfo(user_id, username):
    user = handler.fetch_user(user_id, username)
    premium_status = "✅ <b>Active</b>" if user['premium'] else "❌ <b>Inactive</b>"
    expiry = f"\n🗓️ <i>Expires on:</i> {user['premium_expiry'].split('T')[0]}" if user['premium_expiry'] else ""
    text = (
        "🎼 <b>Your Profile Summary</b>\n"
        "───────────────────────\n"
        f"🆔 <b>User ID:</b> <code>{user['user_id']}</code>\n"
        f"👤 <b>Username:</b> @{user['username']}\n"
        f"📦 <b>Downloads:</b> {user['downloads']}\n"
        f"🎧 <b>Playlists:</b> {len(user['playlists'])}\n"
        f"💎 <b>Premium:</b> {premium_status}{expiry}\n"
        "───────────────────────\n\n"
        "🌟 <i>Upgrade now for unlimited downloads, ad-free music, and more!</i>"
    )
    return text


def playlistInfo(user_id):
    user = handler.fetch_user(user_id)
    playlists = user.get('playlists', [])
    if not playlists:
        return "🎧 <b>No playlists found!</b>\nAdd your favorite songs using /addplaylist 🎶"
    playlist_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(playlists)])
    return (
        f"🎵 <b>Your Playlists</b> ({len(playlists)})\n"
        "───────────────────────\n"
        f"{playlist_text}\n"
        "───────────────────────\n"
        "💡 Use /addplaylist <name> to add more!"
    )


def helper():
    return (
        "<i>Here’s what I can do for you:</i>\n"
        "• 🎵 Search & Download Songs\n"
        "• 🎧 Manage your Playlists\n"
        "• 💎 Free & Premium modes\n"
        "• 📞 Contact admin for upgrades or support\n\n"
        "<code>/start /help /song /addplaylist</code>"
    )


def contact():
    text = (
        "💎 <b>Upgrade to Premium</b>\n"
        "Unlock faster downloads, exclusive playlists, and VIP features!\n\n"
        "🔔 <i>Auto payments are currently unavailable.</i>\n"
        "Please contact our developer for manual subscription plans."
    )
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton('💬 Contact Developer', url='https://t.me/MrDevil_YT'))
    return text, kb


# ================== BOT COMMANDS ==================
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        f"Hello <b>{message.chat.username}</b>! 👋\n"
        "I’m your personal <b>Music Assistant 🎶</b>\n\n"
        "• 🔍 Search & Download songs\n"
        "• 🎧 Manage your Playlists\n"
        "• 💎 Upgrade for unlimited access\n"
        "• 📞 Contact Admin for support\n\n"
        "⬇️ Choose an option below to get started!"
    )
    bot.send_message(message.chat.id, text, reply_markup=mainMenu())


@bot.message_handler(commands=['song'])
def search_song(message):
    query = message.text.replace("/song", "").strip()
    user_id = message.chat.id

    if not query:
        bot.send_message(user_id, "⚠️ Please provide a song name.\nExample: /song Shape of You")
        return

    msg = bot.send_message(user_id, f"🔎 Searching for '{query}' ...")
    try:
        results = yt_handler.search_song(query, limit=5)
    except Exception as e:
        bot.edit_message_text(f"❌ Search failed: {str(e)}", chat_id=user_id, message_id=msg.message_id)
        return

    if not results:
        bot.edit_message_text("❌ No results found!", chat_id=user_id, message_id=msg.message_id)
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for video in results:
        kb.add(InlineKeyboardButton(video['title'], callback_data=f"download:{video['webpage_url']}"))

    bot.edit_message_text("🎶 Select a song to download:", chat_id=user_id, message_id=msg.message_id,
                          reply_markup=kb)


# ================== CALLBACK HANDLER ==================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    user_id = call.from_user.id
    username = call.from_user.username

    if data == 'userinfo':
        bot.send_message(user_id, userInfo(user_id, username))
    elif data == 'playlists_info':
        bot.send_message(user_id, playlistInfo(user_id))
    elif data == 'premium_info':
        text, kb = contact()
        bot.send_message(user_id, text, reply_markup=kb)
    elif data == 'help':
        bot.send_message(user_id, helper())
    elif data.startswith("download:"):
        download_callback(call)


def download_callback(call):
    user_id = call.from_user.id
    url = call.data.split("download:")[1]

    msg = bot.send_message(user_id, "⏳ Downloading... Please wait.")
    try:
        song = yt_handler.download_song(url)
    except Exception as e:
        bot.edit_message_text(f"❌ Download failed: {str(e)}", chat_id=user_id, message_id=msg.message_id)
        return

    try:
        with open(song['file_path'], 'rb') as audio:
            bot.send_audio(user_id, audio, title=song['title'])
        os.remove(song['file_path'])  # cleanup
    except Exception as e:
        bot.send_message(user_id, f"❌ Failed to send audio: {str(e)}")
        return

    bot.edit_message_text(f"✅ Download complete: {song['title']}", chat_id=user_id, message_id=msg.message_id)

    # Update user download count
    user = handler.fetch_user(user_id)
    user['downloads'] += 1
    handler.save_file(user_id, user)


# ================== ADMIN COMMANDS ==================
@bot.message_handler(commands=['grant'])
def grant_premium(message):
    admin_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: <code>/grant &lt;user_id&gt; [months]</code>", parse_mode='HTML')
        return
    user_id = args[1]
    months = int(args[2]) if len(args) > 2 else 1
    result = admin.grant(admin_id, user_id, month=months)
    bot.reply_to(message, result)


@bot.message_handler(commands=['revoke'])
def revoke_premium(message):
    admin_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: <code>/revoke &lt;user_id&gt;</code>", parse_mode='HTML')
        return
    user_id = args[1]
    result = admin.revoke(admin_id, user_id)
    bot.reply_to(message, result)


@bot.message_handler(commands=['extend'])
def extend_premium(message):
    admin_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Usage: <code>/extend &lt;user_id&gt; [months]</code>", parse_mode='HTML')
        return
    user_id = args[1]
    months = int(args[2]) if len(args) > 2 else 1
    result = admin.extend(admin_id, user_id, month=months)
    bot.reply_to(message, result)


@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    admin_id = message.from_user.id
    msg = message.text.replace('/broadcast', '').strip()
    if not msg:
        bot.reply_to(message, "⚠️ Usage: <code>/broadcast &lt;message&gt;</code>", parse_mode='HTML')
        return
    result = admin.broadcast(admin_id, msg, send_func=bot.send_message)
    bot.reply_to(message, result)


# ================== RUN BOT ==================
print("🤖 Music Bot is running...")
bot.infinity_polling()
