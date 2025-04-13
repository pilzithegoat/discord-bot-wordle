import discord
import asyncio
import os
from typing import Dict, Any
from datetime import datetime
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
from discord.ext import commands
from models.game_history import GameHistory
from models.server_config import ServerConfig, Guild
from models.user_settings import UserSettings
from models.daily_challenge import DailyChallenge
from views.leaderboard_views import EnhancedLeaderboardView
from views.history_views import HistoryView, HistorySelectionView
from views.game_views import GameView, EndGameView, MainMenu
from views.settings_views import SettingsView, AnonPasswordModal
from modals.modals import GuessModal, SearchModal
from views.stats_views import StatsView, SearchIDModal
from views.daily_views import DailyChallengeView
from models.achievement_system import AchievementSystem
from models.wordle_game import WordleGame
from models.database import init_db, Session
import random

MAX_ATTEMPTS = 6
MAX_HINTS = 3

class WordleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games: Dict[int, WordleGame] = {}
        self.history = GameHistory()
        self.config = ServerConfig()
        self.settings = UserSettings()
        self.persistent_views_added = False
        self.achievement_system = AchievementSystem()
        self.daily_challenge = DailyChallenge()
        
        # Load words from words.txt
        try:
            with open('words.txt', 'r', encoding='utf-8') as f:
                self.words = [line.strip().upper() for line in f if line.strip()]
        except FileNotFoundError:
            print("Warnung: words.txt nicht gefunden. Verwende Standard-Wörterliste.")
            self.words = [
                "APFEL", "BAUER", "BLUME", "BROTE", "CHAOS", "DICKE", "EICHE", "FALTE", 
                "FARBE", "FISCH", "FLUSS", "GABEL", "GARTE", "GEIST", "GLAS", "HAARE", 
                "HALLE", "HUNDE", "KATZE", "KERZE", "KISTE", "KLEID", "KRONE", "LAMPE", 
                "LINIE", "MALER", "MUSIK", "NACHT", "PAPST", "PFERD", "PILOT", "RADIO", 
                "REGEN", "SAUER", "SCHAF", "SEIDE", "STERN", "TISCH", "VOGEL", "WAGEN", 
                "WALZE", "WASCH", "WERFT", "WOLKE", "ZANGE", "ZEILE", "ZIRKA", "ZITAT"
            ]
        
        init_db()  # Initialize database

    async def add_persistent_views(self):
        if not self.persistent_views_added:
            self.bot.add_view(MainMenu(self))
            self.persistent_views_added = True

    async def display_game(self, interaction: discord.Interaction, game: WordleGame):
        """Zeigt das aktuelle Spiel als embed an"""
        embed = discord.Embed(
            title=f"Wordle - Versuch {MAX_ATTEMPTS - game.remaining}/{MAX_ATTEMPTS}",
            color=discord.Color.blurple()
        )
        
        # Füge bisherige Versuche hinzu
        for i, (guess, result) in enumerate(game.attempts):
            embed.add_field(
                name=f"Versuch {i+1}",
                value=f"`{guess.upper()}`\n{' '.join(result)}",
                inline=False
            )
        
        # Hinweis-Anzeige
        embed.add_field(
            name="Hinweise",
            value=f"`{game.hint_display}`\nGenutzte Tipps: {game.hints_used}/{MAX_HINTS}",
            inline=False
        )
        
        await interaction.edit_original_response(embed=embed)


    @commands.Cog.listener()
    async def on_ready(self):
        await self.add_persistent_views()
        
        for guild in self.bot.guilds:
            if channel_id := self.config.get_wordle_channel(guild.id):
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        # Check if game embed already exists
                        async for message in channel.history(limit=1):
                            if message.embeds and message.embeds[0].title == "🎮 Wordle-Hauptmenü":
                                continue  # Game embed already exists, skip
                        
                        # Clear channel and send new game embed
                        await channel.purge(limit=100)
                        await channel.send(
                            embed=discord.Embed(
                                title="🎮 Wordle-Hauptmenü",
                                description=(
                                    "**Willkommen im Wordle-Hauptmenü!**\n\n"
                                    "▸ 🎮 Starte ein neues Spiel\n"
                                    "▸ 🌞 Tägliche Challenge\n"
                                    "▸ 🏆 Zeige die Bestenlisten an\n"
                                    "▸ 📊 Überprüfe deine Statistiken\n"
                                    "▸ 📜 Durchsuche deine Spielhistorie\n"
                                    "▸ ⚙️ Passe deine Einstellungen an\n"
                                    "▸ ❓ Erhalte Spielhilfe"
                                ),
                                color=discord.Color.blue()
                            ),
                            view=MainMenu(self)
                        )
                    except Exception as e:
                        print(f"Fehler beim Senden der Nachricht: {e}")

        print(f"Wordle cog is ready. Logged in as {self.bot.user}")

    async def on_interaction(self, interaction: discord.Interaction):
        """Globaler Interaktions-Handler"""
        try:
            if interaction.type == discord.InteractionType.component:
            # Füge fehlende Handler hier hinzu
                pass
        except Exception as e:
            print(f"Interaktionsfehler: {str(e)}")
    
    async def add_persistent_views(self):
        if not self.persistent_views_added:
            self.bot.add_view(MainMenu(self))
            self.persistent_views_added = True
    
    async def start_new_game(self, interaction: discord.Interaction):
        """Startet ein neues Wordle-Spiel"""
        if interaction.user.id in self.games:
            await interaction.response.send_message("❌ Du hast bereits ein aktives Spiel!", ephemeral=True)
            return

        # Get random word
        word = random.choice(self.words)
        
        # Create new game with guild_id
        game = WordleGame(word, interaction.guild_id)
        game.start_time = datetime.now()
        self.games[interaction.user.id] = game

        # Create and send game embed
        embed = discord.Embed(
            title="🎮 Neues Wordle-Spiel",
            description=(
                "Errate das 5-Buchstaben-Wort!\n\n"
                "**Farben bedeuten:**\n"
                "🟩 Richtiger Buchstabe\n"
                "🟨 Falsche Position\n"
                "⬛ Nicht im Wort\n\n"
                "**Anonymmodus:** ❌ Inaktiv"
            ),
            color=discord.Color.blue()
        )
        
        view = GameView(self, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    async def show_user_history(self, interaction: discord.Interaction, user: discord.User):
        is_own = interaction.user.id == user.id
        settings = self.settings.get_settings(user.id)
        
        if not is_own and not settings["history_public"]:
            embed = discord.Embed(
                title="🔒 Private Historie",
                description=f"{user.display_name} hat seine Historie privat eingestellt!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = HistoryView(self, user.id, interaction.guild.id)
        embed = view.create_embed()
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def show_own_history(self, interaction: discord.Interaction):
        """Zeigt die eigene Historie des Benutzers an"""
        await self.show_user_history(interaction, interaction.user)

    @app_commands.command(name="historie", description="Zeige Spielverläufe an")
    async def history_command(self, interaction: discord.Interaction):
        """Hauptbefehl für die Historie-Anzeige"""
        embed = discord.Embed(
            title="📜 Historie auswählen",
            description="Wessen Spielhistorie möchtest du einsehen?",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(
            embed=embed,
            view=HistorySelectionView(self),
            ephemeral=True
        )    

    def create_game_embed(self, user_id: int, is_daily: bool = False):  # 👈 Parameter hinzufügen
        settings = self.settings.get_settings(user_id)
        embed = discord.Embed(
            title="�� Neues Wordle-Spiel" if not is_daily else "🌞 Daily Challenge",
            description=f"🔤 Errate das 5-Buchstaben-Wort in 6 Versuchen!\n"
                    f"Anonymmodus: {'✅ Aktiv' if settings['anonymous'] else '❌ Inaktiv'}"
                    + ("\n\n🔥 **Tägliche Herausforderung:**\n- Nur 1 Versuch pro Tag!\n- Globales Leaderboard" if is_daily else ""),
            color=discord.Color.green()
        )
        embed.add_field(
        name="Farben", 
        value="🟩 Richtiger Buchstabe\n🟨 Falsche Position\n⬛ Nicht im Wort", 
        inline=False
        )
        return embed

    @app_commands.command(name="wordle", description="Starte ein neues Wordle-Spiel")
    async def wordle(self, interaction: discord.Interaction):
        await self.start_new_game(interaction)

    @app_commands.command(name="daily", description="Starte die tägliche Challenge")
    async def daily(self, interaction: discord.Interaction):
        await self.handle_daily(interaction)

    @app_commands.command(name="stats", description="Zeige deine Statistiken an")
    async def stats(self, interaction: discord.Interaction):
        await self.show_own_stats(interaction)

    @app_commands.command(name="history", description="Zeige deine Spielhistorie an")
    async def history(self, interaction: discord.Interaction):
        await self.show_own_history(interaction)

    @app_commands.command(name="leaderboard", description="Zeige die Bestenliste an")
    async def leaderboard(self, interaction: discord.Interaction):
        await self.show_leaderboard(interaction)

    @app_commands.command(name="help", description="Zeige die Spielhilfe an")
    async def help(self, interaction: discord.Interaction):
        await self.show_help(interaction)

    @app_commands.command(name="settings", description="Öffne die Einstellungen")
    async def settings(self, interaction: discord.Interaction):
        await self.open_settings(interaction)

    @app_commands.command(name="achievements", description="Zeige deine Achievements")
    async def achievements(self, interaction: discord.Interaction):
        await self._show_achievements(interaction)

    @app_commands.command(name="dailylb", description="Zeige die Daily Challenge Bestenliste")
    async def dailylb(self, interaction: discord.Interaction):
        await self.daily_leaderboard(interaction)

    async def handle_daily(self, interaction: discord.Interaction):
        """Handle Daily Challenge aus dem Menü"""
        user_id = interaction.user.id
        
        if self.daily_challenge.has_played(user_id):
            await interaction.response.send_message(
                "❌ Du hast heute bereits gespielt! Komm morgen wieder!",
                ephemeral=True
            )
            return
        
        if user_id in self.games:
            await interaction.response.send_message("❌ Du hast bereits ein aktives Spiel!", ephemeral=True)
            return
        
        daily_word = self.daily_challenge.get_daily_word()
        game = WordleGame(user_id)
        game.secret_word = daily_word
        self.games[user_id] = game
        
        view = GameView(self, user_id)
        await interaction.response.send_message(
            embed=self.create_game_embed(user_id, is_daily=True),
            view=view
        )

    def get_guild_settings(self, guild_id: int) -> dict:
        """Holt die Server-Einstellungen aus der Datenbank"""
        try:
            with Session() as session:
                guild = session.query(Guild).filter_by(id=guild_id).first()
                if guild:
                    return {
                        "max_hints": guild.max_hints,
                        "max_attempts": guild.max_attempts
                    }
        except Exception as e:
            print(f"Fehler beim Laden der Server-Einstellungen: {e}")
        return None

    async def setup(self):
        """Registriert die Commands beim Bot"""
        self.bot.add_command(self.wordle)
        self.bot.add_command(self.daily)
        self.bot.add_command(self.stats)
        self.bot.add_command(self.history)
        self.bot.add_command(self.leaderboard)
        self.bot.add_command(self.help)
        self.bot.add_command(self.settings)
        self.bot.add_command(self.achievements)
        self.bot.add_command(self.dailylb)