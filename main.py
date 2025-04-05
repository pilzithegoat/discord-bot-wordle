import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from cogs.wordle_cog import WordleCog
from views.game_views import MainMenu

# Worde Variablen. When use one do a # behind the variable and write # - used
load_dotenv()
Token = os.getenv("TOKEN") # - used
MAX_HINTS = int(os.getenv("MAX_HINTS", 0))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 0))
WORDS_FILE = os.getenv("WORDS_FILE")
DATA_FILE = os.getenv("DATA_FILE")
CONFIG_FILE = os.getenv("CONFIG_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
DAILY_FILE = os.getenv("DAILY_FILE")


if not os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "w") as f:
        f.write("\n".join(["apfel", "birne", "banane", "mango", "beere"]))

with open(WORDS_FILE) as f:
    WORDS = [w.strip().lower() for w in f.readlines() if len(w.strip()) == 5]

if not WORDS:
    raise ValueError("Keine gültigen Wörter in der Datei!")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():

    activity = discord.Activity(
        name="Wordle 🟩🟨", 
        type=discord.ActivityType.listening
    )
    await bot.change_presence(activity=activity)

    try:
        await bot.add_cog(WordleCog(bot))
        print(f"{bot.user} ist bereit!")
        
        cog = bot.get_cog("WordleCog")
        for guild in bot.guilds:
            if channel_id := cog.config.get_wordle_channel(guild.id):
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.purge(limit=1)
                        await channel.send(
                            embed=discord.Embed(
                                title="🎮 Wordle-Hauptmenü",
                                description=(
                                    "**Willkommen im Wordle-Hauptmenü!**\n\n"
                                    "▸ 🎮 Starte ein neues Spiel\n"
                                    "▸ 🏆 Zeige die Bestenliste an\n"
                                    "▸ 📊 Überprüfe deine Statistiken\n"
                                    "▸ 📜 Durchsuche deine Spielhistorie\n"
                                    "▸ ⚙️ Passe deine Einstellungen an\n"
                                    "▸ ❓ Erhalte Spielhilfe"
                                ),
                                color=discord.Color.blue()
                            ),
                            view=MainMenu(cog)
                        )
                    except Exception as e:
                        print(f"Fehler: {str(e)}")
                        
    except Exception as e:
        print(f"Startfehler: {str(e)}")

if __name__ == "__main__":
    bot.run(Token)