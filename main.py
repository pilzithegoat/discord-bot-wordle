import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from cogs.wordle_cog import WordleCog

load_dotenv()
WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(WordleCog(bot))
    print(f"{bot.user} ist bereit!")



if __name__ == "__main__":
    if not os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "w") as f:
            f.write("\n".join(["apfel", "birne", "banane", "mango", "beere"]))
    
    with open(WORDS_FILE) as f:
        WORDS = [w.strip().lower() for w in f.readlines() if len(w.strip()) == 5]
    
    if not WORDS:
        raise ValueError("Keine gültigen Wörter in der Datei!")
    
    bot.run("")