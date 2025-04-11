import os
import telebot
import json
from datetime import datetime, timedelta
from telebot import types

print("🚀 Bot is starting...")

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("❌ BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5806222268
GAMES_FILE = "games.json"

# 🔄 Load games from JSON file
def load_games():
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "r") as f:
            return json.load(f)
    return []

# 💾 Save games to JSON file
def save_games(games):
    with open(GAMES_FILE, "w") as f:
        json.dump(games, f, indent=4)

# 📦 Initial games data load
games_list = load_games()

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = """
    👋 Welcome to the GameBot!

    🚀 Discover & download awesome games.

    🔍 Send a game name or category (e.g. **'racing games'**, **'zombie'**).

    💬 Commands:
    - /games – List all available games.
    - /add_game – Add a new game (Admin only)
    - /remove_game – Remove a game (Admin only)
    - /edit_game – Edit a game (Admin only)
    - /top_games – Weekly top downloaded games
    - /reset_downloads – Reset download counts (Admin only)
    - /download_report – Full download report (Admin only)
    
    🎮 Let the fun begin!
    """
    bot.reply_to(message, welcome_message)

# /add_game command (admin only)
@bot.message_handler(commands=['add_game'])
def add_game(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not authorized to add games.")
        return

    try:
        text_lines = message.text.split('\n')
        name = link = description = ""
        category = []

        for line in text_lines:
            if line.lower().startswith("game name:-"):
                name = line.split("-", 1)[1].strip().lower()
            elif line.lower().startswith("download here:-"):
                link = line.split("-", 1)[1].strip()
            elif line.lower().startswith("short intro:-"):
                description = line.split("-", 1)[1].strip()
            elif line.lower().startswith("category:-"):
                category = line.split("-", 1)[1].strip().lower().split(",")
            elif description != "":
                description += "\n" + line.strip()

        category = [cat.strip() for cat in category]
        description = description.strip().replace("\n", " ")

        if not name or not link or not description or not category:
            bot.reply_to(message, "❌ Invalid format. Use:\n\n/add_game\nGame Name:- Name\nDownload Here:- link\nShort Intro:- description\nCategory:- category1, category2")
            return

        game_data = {
            "name": name,
            "link": link,
            "description": description,
            "category": category,
            "downloads": 0,
            "last_downloaded": ""
        }

        games_list.append(game_data)
        save_games(games_list)

        bot.reply_to(message, f"✅ Game '{name.title()}' added successfully!")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# /remove_game
@bot.message_handler(commands=['remove_game'])
def remove_game(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You are not authorized to remove games.")

    try:
        name = message.text.replace('/remove_game', '').strip().lower()
        global games_list
        games_list = [g for g in games_list if g['name'] != name]
        save_games(games_list)
        bot.reply_to(message, f"✅ Game '{name}' removed.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# /edit_game
@bot.message_handler(commands=['edit_game'])
def edit_game(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ You are not authorized to edit games.")

    try:
        text_lines = message.text.split('\n')
        name = link = description = ""
        category = []

        for line in text_lines:
            if line.lower().startswith("game name:-"):
                name = line.split("-", 1)[1].strip().lower()
            elif line.lower().startswith("download here:-"):
                link = line.split("-", 1)[1].strip()
            elif line.lower().startswith("short intro:-"):
                description = line.split("-", 1)[1].strip()
            elif line.lower().startswith("category:-"):
                category = line.split("-", 1)[1].strip().lower().split(",")
            elif description != "":
                description += "\n" + line.strip()

        description = description.strip().replace("\n", " ")
        category = [c.strip() for c in category]

        for game in games_list:
            if game['name'] == name:
                game['link'] = link or game['link']
                game['description'] = description or game['description']
                game['category'] = category or game['category']
                break
        else:
            return bot.reply_to(message, "❌ Game not found.")

        save_games(games_list)
        bot.reply_to(message, f"✅ Game '{name.title()}' updated.")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# /reset_downloads
@bot.message_handler(commands=['reset_downloads'])
def reset_downloads(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Not allowed!")
    for game in games_list:
        game['downloads'] = 0
        game['last_downloaded'] = ""
    save_games(games_list)
    bot.reply_to(message, "🔁 All download counts reset.")

# /top_games
@bot.message_handler(commands=['top_games'])
def top_games(message):
    week_ago = datetime.now() - timedelta(days=7)
    top = sorted([g for g in games_list if g['last_downloaded'] and datetime.strptime(g['last_downloaded'], "%Y-%m-%d") >= week_ago], key=lambda g: g['downloads'], reverse=True)
    if not top:
        return bot.reply_to(message, "📭 No downloads in the past week.")

    msg = "🔥 *Top Games This Week:*\n\n"
    for game in top[:5]:
        msg += f"🎮 *{game['name'].title()}* — {game['downloads']} downloads\n"
    bot.reply_to(message, msg, parse_mode='Markdown')

# /download_report
@bot.message_handler(commands=['download_report'])
def download_report(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Not allowed!")

    msg = "📊 *Download Report:*\n\n"
    for g in games_list:
        msg += f"• {g['name'].title()} - {g['downloads']} downloads\n"
    bot.reply_to(message, msg, parse_mode='Markdown')

print("✅ Bot Started")
bot.polling(none_stop=True)
