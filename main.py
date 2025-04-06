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
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
presence_counter = 0

def get_total_players():
    """Gibt die korrekte Anzahl mit angepasster Grammatik zurück"""
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=30)
        
        with open(DATA_FILE) as f:
            data = json.load(f)
            global_users = data.get("global", {}).get("users", {})
            
            active_players = set()
            
            for user_id, spiele in global_users.items():
                if spiele:
                    latest_game = max(spiele, key=lambda x: datetime.datetime.fromisoformat(x["timestamp"]))
                    game_time = datetime.datetime.fromisoformat(latest_game["timestamp"])
                    if game_time > cutoff_date:
                        active_players.add(user_id)
            
            count = len(active_players)
            return f"{count} aktiver Spieler" if count == 1 else f"{count} aktive Spieler"
            
    except Exception as e:
        print(f"Spielerzählfehler: {e}")
        return "0 aktive Spieler"

def get_best_player():
    """Berechnet den besten Spieler mit Priorisierung: 1. Siege, 2. Versuche, 3. Tipps"""
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(hours=24)
        
        with open(DATA_FILE) as f:
            data = json.load(f)
            global_users = data.get("global", {}).get("users", {})
            
            player_stats = []
            
            for user_id, all_games in global_users.items():
                # Filtere gewonnene Spiele der letzten 24h
                won_games = [
                    g for g in all_games 
                    if g.get("won", False) 
                    and datetime.datetime.fromisoformat(g["timestamp"]) > cutoff_date
                ]
                
                if not won_games:
                    continue

                total_wins = len(won_games)
                total_attempts = sum(g["attempts"] for g in won_games)
                total_hints = sum(g["hints"] for g in won_games)
                avg_attempts = total_attempts / total_wins
                avg_hints = total_hints / total_wins
                
                # Sortierkriterien:
                # 1. Meiste Siege (absteigend durch -total_wins)
                # 2. Wenigste Versuche/Sieg (aufsteigend)
                # 3. Wenigste Tipps/Sieg (aufsteigend)
                player_stats.append((
                    -total_wins,    # Primärschlüssel 
                    avg_attempts,   # Sekundärschlüssel
                    avg_hints,      # Tertiärschlüssel
                    user_id
                ))
            
            if not player_stats:
                return "Werde der/die Erste!", 0, 0, 0
            
            player_stats.sort()
            
            # Debug-Ausgabe
            print("\n🏆 Rangliste:")
            for i, stats in enumerate(player_stats[:3]):
                print(f"{i+1}. {stats[3][-4:]} "
                      f"| Siege: {-stats[0]} "
                      f"| Ø-Versuche: {stats[1]:.1f} "
                      f"| Ø-Tipps: {stats[2]:.1f}")
            
            bester = player_stats[0]
            user = bot.get_user(int(bester[3]))
            name = user.name if user else f"Spieler {bester[3][-4:]}"
            
            return name, -bester[0], bester[1], bester[2]
            
    except Exception as e:
        print(f"Bester-Spieler-Error: {str(e)}")
        return "Fehler in der Berechnung", 0, 0, 0
    
async def update_presence():
    await bot.wait_until_ready()
    global presence_counter
    
    stats = [
        ("🕒 Online seit", lambda t: t),
        ("🌐 Auf", lambda _: f"{len(bot.guilds)} Servern"),
        ("👥", lambda _: get_total_players()),
        ("🏆 Beste:r", lambda _: f"{get_best_player()[0]} ({get_best_player()[1]}×)")
    ]

    while not bot.is_closed():
        try:
            uptime = datetime.datetime.now() - bot.start_time
            time_str = f"{uptime.days}d {uptime.seconds//3600:02d}h {(uptime.seconds//60)%60:02d}m"
            
            current_stat = stats[presence_counter % len(stats)]
            main_text = f"{current_stat[0]} {current_stat[1](time_str)}"
            
            activity = discord.Activity(
                name=main_text,
                type=discord.ActivityType.listening
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
    print(f"Initiale Spieler: {get_player_count()}")
    print(f"Serveranzahl: {len(bot.guilds)}")

    try:
        await bot.add_cog(WordleCog(bot))
        print(f"Bot Ready {bot.is_ready}")
        
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

    except Exception as e:
        print(f"Startfehler: {str(e)}")

if __name__ == "__main__":
    bot.run(Token)
