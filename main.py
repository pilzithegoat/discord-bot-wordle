import discord
import os
import asyncio
import datetime
import json
from pathlib import Path
from discord.ext import commands
from cogs.wordle_cog import WordleCog
from views.game_views import MainMenu
from dashboard.app import app
import threading
import sys
from models.database import init_db, Session, Game
from cogs import setup
from werkzeug.serving import make_server

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import configuration from config.py
try:
    from config import (
        TOKEN, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, ADMIN_IDS,
        FLASK_SECRET_KEY, FLASK_APP, FLASK_ENV, MAX_HINTS, MAX_ATTEMPTS,
        DISCORD_REDIRECT_URI
    )
except ImportError:
    print("Error: config.py not found. Please run install.sh first.")
    sys.exit(1)

# Bot configuration
Token = TOKEN
MAX_HINTS = MAX_HINTS
MAX_ATTEMPTS = MAX_ATTEMPTS
WORDS_FILE = "words.txt"
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_challenge.json"
COUNT_FILE = "game_count.json"
CUSTOM_ACTIVITY = None

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
presence_counter = 0
flask_server = None

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
                    "wins": 0,
                    "total_attempts": 0,
                    "games": 0
                }
            player_stats[game.user_id]["wins"] += 1
            player_stats[game.user_id]["total_attempts"] += game.attempts
            player_stats[game.user_id]["games"] += 1
        
        # Finde den besten Spieler
        best_player_id = max(
            player_stats.items(),
            key=lambda x: (x[1]["wins"], -x[1]["total_attempts"] / x[1]["games"])
        )[0]
        
        best_stats = player_stats[best_player_id]
        avg_attempts = best_stats["total_attempts"] / best_stats["games"]
        
        session.close()
        return f"<@{best_player_id}>", best_stats["wins"], avg_attempts, best_stats["games"]
            
    except Exception as e:
        print(f"Bestenliste Fehler: {e}")
        return "Sei du doch der Beste!", 0, 0, 0

async def update_presence():
    """Aktualisiert den Bot-Status regelmäßig"""
    global presence_counter
    
    while True:
        try:
            if presence_counter % 2 == 0:
                total_players = get_total_players()
                await bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=total_players
                    )
                )
            else:
                best_player, wins, avg_attempts, games = get_best_player()
                if wins > 0:
                    await bot.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name=f"{best_player} mit {wins} Siegen"
                        )
                    )
                else:
                    await bot.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name="wer der Beste wird"
                        )
                    )
            
            presence_counter += 1
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Status Update Fehler: {e}")
            await asyncio.sleep(30)

@bot.event
async def on_ready():
    """Wird ausgeführt, wenn der Bot bereit ist"""
    print(f"{bot.user} ist online!")
    
    # Starte das Status-Update
    asyncio.create_task(update_presence())
    
    # Lade die Cogs
    await setup(bot)
    
    # Starte den Flask-Server in einem separaten Thread
    global flask_server
    flask_server = make_server('0.0.0.0', 5000, app)
    flask_thread = threading.Thread(target=flask_server.serve_forever)
    flask_thread.daemon = True
    flask_thread.start()
    print("Flask-Server gestartet auf http://0.0.0.0:5000")

async def main():
    """Hauptfunktion zum Starten des Bots"""
    try:
        # Starte den Bot
        await bot.start(Token)
    except Exception as e:
        print(f"Fehler beim Starten des Bots: {e}")
        if flask_server:
            flask_server.shutdown()
        await bot.close()

if __name__ == "__main__":
    # Starte den Bot
    asyncio.run(main())