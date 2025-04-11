import os
import telebot
from pymongo import MongoClient

# Debugging to check Railway Startup
print("🚀 Bot is starting...")

# Get token from environment
TOKEN = os.getenv("BOT_TOKEN")  # Bot token from Railway variables
if not TOKEN:
    raise Exception("❌ BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(TOKEN)

# MongoDB URI and client setup
uri = "mongodb+srv://Bilalhussain1236597:Bilalhussain2211@cluster0.twqxhc4.mongodb.net/gamesDB?retryWrites=true&w=majority"
try:
    client = MongoClient(uri)
    db = client['gamesDB']
    games_collection = db['games']
    print("✅ MongoDB Connected")
except Exception as e:
    print("❌ MongoDB connection error:", e)
    raise e

# Admin ID
ADMIN_ID = 5806222268

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_message = """
    👋 Welcome to the GameBot!

    🚀 Here you can easily search and discover new games.

    🔍 **How to use:**
    - Send me a game name or category (e.g. **'racing games'**, **'action games'**).
    - I’ll give you details about the game including a download link.

    💬 **Commands:**
    - **/games** – To see a list of available games.
    - **/add_game** – To add a new game (Admin Only).

    Let's find your next favorite game! 🎮
    """
    bot.reply_to(message, welcome_message)

# /add_game command handler
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
                name = line.split(":-", 1)[1].strip().lower()
            elif line.lower().startswith("download here:-"):
                link = line.split(":-", 1)[1].strip()
            elif line.lower().startswith("short intro:-"):
                description = line.split(":-", 1)[1].strip()
            elif line.lower().startswith("category:-"):
                category = line.split(":-", 1)[1].strip().lower().split(",")
            elif description != "":
                description += "\n" + line.strip()

        category = [cat.strip() for cat in category]
        description = description.strip().replace("\n", " ")

        if not name or not link or not description or not category:
            bot.reply_to(message, "❌ Invalid format. Please use this format:\n\n/add_game\nGame Name:- Name\nDownload Here:- link\nShort Intro:- description\nCategory:- category1, category2, category3")
            return

        # Insert data into MongoDB
        game_data = {
            "name": name,
            "link": link,
            "description": description,
            "category": category
        }
        games_collection.insert_one(game_data)

        bot.reply_to(message, f"✅ Game '{name.title()}' added successfully under categories: {', '.join(category).title()}!")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# /games command to show games
@bot.message_handler(commands=['games'])
def show_games(message):
    games = games_collection.find()

    if games.count() == 0:
        bot.reply_to(message, "❌ No games added yet.")
        return

    game_list = "📋 Available Games:\n"
    for game in games:
        game_list += f"- {game['name'].title()} ({', '.join(game['category']).title()})\n"

    bot.reply_to(message, game_list)

# Search game or category
@bot.message_handler(func=lambda message: True)
def handle_input(message):
    text = message.text.strip().lower()

    # Searching by category
    matching_by_category = games_collection.find({"category": {"$in": [text]}})

    if matching_by_category.count() > 0:
        response = f"📂 Games in '{text.title()}' category:\n"
        for game in matching_by_category:
            response += f"\n🎮 {game['name'].title()}\n{game['description']}\n🔗 {game['link']}\n"
        bot.send_message(message.chat.id, response)
        return

    # Searching by game name
    matching_by_name = games_collection.find({"name": {"$regex": text, "$options": "i"}})

    if matching_by_name.count() > 0:
        response = ""
        for game in matching_by_name:
            response += f"🎮 {game['name'].title()}\n\n{game['description']}\n\n🔗 Download Link:\n{game['link']}\n\n"
        bot.send_message(message.chat.id, response)
        return

    bot.reply_to(message, "❌ No game or category found. Try another name or category.")

print("✅ Bot Started")
bot.polling(none_stop=True)
