import discord
import os
import asyncio
import datetime
import json
from pathlib import Path
from dotenv import load_dotenv
from discord.ext import commands
from cogs.wordle_cog import WordleCog
from views.game_views import MainMenu
from dashboard.app import app
import threading
import sys
from models.database import init_db, Session, Game
from cogs import setup

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
load_dotenv()

# Bot configuration
Token = os.getenv("TOKEN")
MAX_HINTS = int(os.getenv("MAX_HINTS", 0))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 0))
WORDS_FILE = os.getenv("WORDS_FILE")
DATA_FILE = os.getenv("DATA_FILE")
CONFIG_FILE = os.getenv("CONFIG_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
DAILY_FILE = os.getenv("DAILY_FILE")
COUNT_FILE = os.getenv("COUNT_FILE")
CUSTOM_ACTIVITY = os.getenv("CUSTOM_ACTIVITY", None)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "your_secret_key_here")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")

if not os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "w") as f:
        f.write("\n".join(["apfel", "birne", "banane", "mango", "beere"]))

with open(WORDS_FILE) as f:
    WORDS = [w.strip().lower() for w in f.readlines() if len(w.strip()) == 5]

if not WORDS:
    raise ValueError("Keine gültigen Wörter in der Datei!")

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
presence_counter = 0

def get_total_players():
    """Gibt die korrekte Anzahl mit angepasster Grammatik zurück"""
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)
        session = Session()
        
        # Zähle eindeutige Benutzer, die in den letzten 30 Tagen gespielt haben
        active_players = session.query(Game.user_id).filter(
            Game.timestamp >= cutoff_date,
            Game.anonymous == False
        ).distinct().count()
        
        session.close()
        
        return f"{active_players} aktiver Spieler" if active_players == 1 else f"{active_players} aktive Spieler"
            
    except Exception as e:
        print(f"Spielerzählfehler: {e}")
        return "0 aktive Spieler"

def get_best_player():
    """Gibt den besten Spieler zurück oder motiviert zur Teilnahme bei fehlenden Daten"""
    try:
        session = Session()
        cutoff_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        
        # Hole alle gewonnenen Spiele der letzten 24 Stunden
        won_games = session.query(Game).filter(
            Game.won == True,
            Game.timestamp >= cutoff_date,
            Game.anonymous == False
        ).all()
        
        if not won_games:
            session.close()
            return "Sei du doch der Beste!", 0, 0, 0
        
        # Gruppiere Spiele nach Benutzer
        player_stats = {}
        for game in won_games:
            if game.user_id not in player_stats:
                player_stats[game.user_id] = {
                    'wins': 0,
                    'total_attempts': 0,
                    'total_hints': 0
                }
            
            stats = player_stats[game.user_id]
            stats['wins'] += 1
            stats['total_attempts'] += game.attempts
            stats['total_hints'] += game.hints_used
        
        # Berechne Durchschnittswerte und sortiere
        player_rankings = []
        for user_id, stats in player_stats.items():
            avg_attempts = stats['total_attempts'] / stats['wins']
            avg_hints = stats['total_hints'] / stats['wins']
            
            player_rankings.append((
                -stats['wins'],     # Meiste Siege zuerst
                avg_attempts,       # Wenigste Versuche
                avg_hints,          # Wenigste Tipps
                user_id
            ))
        
        session.close()
        
        if not player_rankings:
            return "Sei du doch der Beste!", 0, 0, 0
        
        player_rankings.sort()
        bester = player_rankings[0]
        user = bot.get_user(int(bester[3]))
        name = user.name if user else f"Spieler {bester[3]}"
        
        # Debug-Ausgabe
        print(f"\n🔍 Aktueller Topspieler: {name}")
        print(f"🏆 Siege: {-bester[0]}")
        print(f"🎯 Ø-Versuche: {bester[1]:.1f}")
        print(f"💡 Ø-Tipps: {bester[2]:.1f}")
        
        return name, -bester[0], bester[1], bester[2]
        
    except Exception as e:
        print(f"⚠️ Unerwarteter Fehler: {str(e)}")
        return "Werde du doch Topspieler!", 0, 0, 0

async def update_presence():
    await bot.wait_until_ready()
    global presence_counter
    
    stats = [
        ("🕒 Online seit", lambda t: t),
        
        ("🌐 Auf", lambda _: f"{len(bot.guilds)} Servern"),
        ("👥", lambda _: get_total_players()),
        ("🏆 Beste:r", lambda _: (lambda res: f"{res[0]} ({res[3]} Siege)")(get_best_player()))
    ]

    while not bot.is_closed():
        try:
            uptime = datetime.datetime.now() - bot.start_time
            time_str = f"{uptime.days}d {uptime.seconds//3600:02d}h {(uptime.seconds//60)%60:02d}m"
            
            current_stat = stats[presence_counter % len(stats)]
            main_text = f"{current_stat[0]} {current_stat[1](time_str)}"
            
            activity = discord.Activity(
                name=main_text,
                type=discord.ActivityType.watching
            )
            
            await bot.change_presence(activity=activity)
            presence_counter += 1
            
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"Presence-Fehler: {str(e)}")
            await asyncio.sleep(30)

@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now()
    print(f"Gestartet um: {bot.start_time}")
    print(f"Serveranzahl: {len(bot.guilds)}")

    try:
        await bot.add_cog(WordleCog(bot))
        print(f"Bot Ready")
        
        cog = bot.get_cog("WordleCog")
        for guild in bot.guilds:
            if channel_id := cog.config.get_wordle_channel(guild.id):
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.purge(limit=None)
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
                        
        bot.loop.create_task(update_presence())
        await setup(bot)

    except Exception as e:
        print(f"Startfehler: {str(e)}")

def run_flask():
    """Run the Flask app in a separate thread"""
    app.config['BOT'] = bot
    app.config['BOT_TOKEN'] = Token
    app.config['MAX_HINTS'] = MAX_HINTS
    app.config['MAX_ATTEMPTS'] = MAX_ATTEMPTS
    app.config['WORDS_FILE'] = WORDS_FILE
    app.config['CONFIG_FILE'] = CONFIG_FILE
    app.config['DISCORD_CLIENT_ID'] = DISCORD_CLIENT_ID
    app.config['DISCORD_CLIENT_SECRET'] = DISCORD_CLIENT_SECRET
    app.config['DISCORD_REDIRECT_URI'] = DISCORD_REDIRECT_URI
    app.config['ADMIN_IDS'] = ADMIN_IDS
    
    app.run(host='0.0.0.0', port=5000, debug=False)

def run_dashboard():
    """Start the Flask dashboard"""
    print("Starting Flask dashboard...")
    app.config['BOT'] = bot
    app.config['BOT_TOKEN'] = Token
    app.config['MAX_HINTS'] = MAX_HINTS
    app.config['MAX_ATTEMPTS'] = MAX_ATTEMPTS
    app.config['WORDS_FILE'] = WORDS_FILE
    app.config['CONFIG_FILE'] = CONFIG_FILE
    app.config['DISCORD_CLIENT_ID'] = DISCORD_CLIENT_ID
    app.config['DISCORD_CLIENT_SECRET'] = DISCORD_CLIENT_SECRET
    app.config['DISCORD_REDIRECT_URI'] = DISCORD_REDIRECT_URI
    app.config['ADMIN_IDS'] = ADMIN_IDS
    
    app.run(host='0.0.0.0', port=5000, debug=False)

async def main():
    try:
        await bot.start(Token)
    except Exception as e:
        print(f"Fehler beim Starten des Bots: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Create threads for bot and dashboard
    bot_thread = threading.Thread(target=run_flask)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Wait for the bot thread to complete
    bot_thread.join()
    
    asyncio.run(main())