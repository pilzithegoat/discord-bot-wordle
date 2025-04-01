import discord
import asyncio
import os
from typing import Dict, Any
from datetime import datetime
from discord.ui import View, Button, Select, Modal, TextInput
from discord import app_commands
from discord.ext import commands
from models.game_history import GameHistory
from models.server_config import ServerConfig
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
from models.daily_challenge import DailyChallenge
from models.wordle_game import WordleGame

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
        self.achievement_system = AchievementSystem(self)
        self.daily_challenge = DailyChallenge()

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
                                    "▸ ❓ Erhalte Spielhilfe\n"
                                    "▸ 🔍 Finde andere Spieler"
                                ),
                                color=discord.Color.blue()
                            ),
                            view=MainMenu(self)
                        )
                    except Exception as e:
                        print(f"Fehler beim Senden der Nachricht: {e}")

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
        if interaction.user.id in self.games:
            await interaction.response.send_message("❌ Du hast bereits ein aktives Spiel!", ephemeral=True)
            return
        
        self.games[interaction.user.id] = WordleGame(interaction.user.id)
        view = GameView(self, interaction.user.id)
        await interaction.response.send_message(embed=self.create_game_embed(interaction.user.id), view=view)

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
            title="🎮 Neues Wordle-Spiel" if not is_daily else "🌞 Daily Challenge",
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
    
    @app_commands.command(name="wordle_setup", description="Richte den Wordle-Channel ein")
    @app_commands.default_permissions(administrator=True)
    async def wordle_setup(self, interaction: discord.Interaction):
        self.config.set_wordle_channel(interaction.guild_id, interaction.channel_id)
        try:
            await interaction.channel.purge(limit=1)
        except: pass
        await interaction.channel.send(
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
        await interaction.response.send_message("✅ Channel eingerichtet!", ephemeral=True)
    
    async def handle_process_guess(self, interaction: discord.Interaction, guess: str, is_daily=False):
        game = self.games.get(interaction.user.id)
        if not game:
            await interaction.response.send_message("❌ Starte erst ein Spiel!", ephemeral=True)
            return
        
        if len(guess) != 5 or not guess.isalpha():
            await interaction.response.send_message("❌ Ungültige Eingabe!", ephemeral=True)
            return
        
        result = game.check_guess(guess.lower())
        embed = discord.Embed(
            title=f"Versuche übrig: {game.remaining}",
            color=discord.Color.blurple()
        )

        if is_daily:
            daily_word = self.daily_challenge.get_daily_word()
            if guess.lower() != daily_word:
                await interaction.response.send_message("❌ Falsches Wort für die Daily Challenge!", ephemeral=True)
            return
        
        
        for i, (attempt, res) in enumerate(game.attempts):
            embed.add_field(name=f"Versuch {i+1}", value=f"{attempt.upper()}\n{' '.join(res)}", inline=False)
        
        embed.add_field(name="Hinweis", value=f"`{game.hint_display}`", inline=False)
        
        if guess.lower() == game.secret_word or game.remaining == 0:
            await self.handle_end_game(interaction, guess.lower() == game.secret_word, is_daily=is_daily)
        else:
            view = GameView(self, interaction.user.id)
            await interaction.response.edit_message(embed=embed, view=view)
    
    async def handle_give_hint(self, interaction: discord.Interaction):
        game = self.games.get(interaction.user.id)
        if not game or not game.add_hint():
            await interaction.response.send_message("❌ Keine Tipps mehr verfügbar!", ephemeral=True)
            return
        
        embed = interaction.message.embeds[0]
        embed.set_field_at(-1, name="Hinweis", value=f"`{game.hint_display}`", inline=False)
        view = GameView(self, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @app_commands.command(name="daily", description="Tägliche Herausforderung")
    async def daily_command(self, interaction: discord.Interaction):
        """Handle Daily Challenge mit speziellem Embed"""
        if interaction.user.id in self.games:
            await interaction.response.send_message("❌ Du hast bereits ein aktives Spiel!", ephemeral=True)
            return
        
        # Daily-spezifisches Spiel erstellen
        self.games[interaction.user.id] = WordleGame(interaction.user.id)
        self.games[interaction.user.id].secret_word = self.daily_challenge.get_daily_word()
        
        view = GameView(self, interaction.user.id)
        await interaction.response.send_message(
            embed=self.create_game_embed(interaction.user.id, is_daily=True),
            view=view
        )

    async def handle_end_game(self, interaction: discord.Interaction, won: bool, is_daily: bool = False):
        game = self.games.pop(interaction.user.id, None)
        if not game:
            return
        
        new_achievements = self.achievement_system.check_achievements(interaction.user.id, game)
        
        self.history.add_game(interaction.guild_id, interaction.user.id, {
            "won": won,
            "word": game.secret_word,
            "guesses": game.attempts,
            "hints": game.hints_used,
            "duration": game.get_duration()
        })
        
        settings = self.settings.get_settings(interaction.user.id)
        embed = discord.Embed(
            title="🎉 Gewonnen!" if won else "💥 Verloren!",
            description=f"Das Wort war: ||{game.secret_word.upper()}||",
            color=discord.Color.green() if won else discord.Color.red()
        )
        
        if settings["anonymous"]:
            anon_id = settings.get("anon_id", "UNKNOWN")
            embed.set_footer(text=f"Anonyme ID: {anon_id}")
            embed.add_field(name="Spielmodus", value="🎭 Anonymes Spiel", inline=False)
        else:
            embed.add_field(name="Spielmodus", value="🔓 Öffentliches Spiel", inline=False)
        
        view = EndGameView(self, interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)
        await asyncio.sleep(10)
        try:
            await interaction.delete_original_response()
        except:
            pass

        if is_daily:
            self.daily_challenge.add_participant(interaction.user.id, len(game.attempts))
            embed.add_field(name="Daily Challenge", 
                      value=f"🏆 Du bist Platz {self.get_daily_rank(interaction.user.id)}!",
                      inline=False)

        if game.secret_word == self.daily_challenge.get_daily_word():
            self.daily_challenge.add_participant(interaction.user.id, len(game.attempts))

        if new_achievements:
            achievements_text = "\n".join(f"🎉 {a['name']}: {a['description']}" for a in new_achievements)
            embed.add_field(name="Neue Achievements freigeschaltet!", value=achievements_text, inline=False)
    
    def get_daily_rank(self, user_id: int):
        leaderboard = self.daily_challenge.get_leaderboard()
        user_str = str(user_id)
        return next((i+1 for i, (u_id, _) in enumerate(leaderboard) if u_id == user_str), None)

    async def show_stats(self, interaction: discord.Interaction, user: discord.User):
        is_own_stats = interaction.user.id == user.id
        settings = self.settings.get_settings(user.id)
    
        if not is_own_stats and not settings["stats_public"]:
            await interaction.response.send_message("❌ Diese Statistiken sind privat!", ephemeral=True)
            return
    
        public_games = [g for g in self.history.get_user_games(user.id, "global") if not g.get("anonymous", False)]
        anon_games = self.history.get_anonymous_games(settings["anon_id"])
    
        embed = discord.Embed(
            title=f"📊 Statistiken",
            color=discord.Color.gold()
        )
    
        if public_games or anon_games:
            # Kopf entfernt - nur noch "Anonyme Spiele" als Unterscheidung
            if public_games:
                embed.add_field(name="Öffentliche Spiele", 
                            value=f"✅ {sum(g['won'] for g in public_games)} Siege\n"
                                    f"❌ {len(public_games)-sum(g['won'] for g in public_games)} Niederlagen\n"
                                    f"📊 {sum(g['won'] for g in public_games)/len(public_games)*100:.1f}% Winrate",
                            inline=True)
        
            if anon_games:
                embed.add_field(name="🎭 Anonyme Spiele", 
                            value=f"✅ {sum(g['won'] for g in anon_games)} Siege\n"
                                    f"❌ {len(anon_games)-sum(g['won'] for g in anon_games)} Niederlagen\n"
                                    f"📊 {sum(g['won'] for g in anon_games)/len(anon_games)*100:.1f}% Winrate",
                            inline=True)
        else:
            embed.description = "📭 Noch keine Spiele gespielt!"
    
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_anon_history(self, interaction: discord.Interaction, user: discord.User):
        settings = self.settings.get_settings(user.id)
        if not settings["anon_password"]:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Es wurde kein Anonym-Passwort gesetzt!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Es wurde kein Anonym-Passwort gesetzt!", ephemeral=True)
            return
        
        view = HistoryView(self, user.id, interaction.guild.id)
        await interaction.response.send_modal(AnonPasswordModal(self, user.id, view))
    
    async def show_history(self, interaction: discord.Interaction, user: discord.User):
        is_own_history = interaction.user.id == user.id
        settings = self.settings.get_settings(user.id)
        
        if not is_own_history and not settings["history_public"]:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Diese Historie ist privat!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Diese Historie ist privat!", ephemeral=True)
            return
        
        view = HistoryView(self, user.id, interaction.guild.id)
        if interaction.response.is_done():
            await interaction.followup.send(embed=view.create_embed(), view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)
    
    async def show_leaderboard(self, interaction: discord.Interaction):
        """Zeigt die Bestenliste nur dem aufrufenden Spieler"""
        try:
            await interaction.response.defer(ephemeral=True)
        # Korrekte Parameter: cog, interaction, guild_id, scope
            view = EnhancedLeaderboardView(self, interaction, interaction.guild_id, "server")
            await interaction.followup.send(
            embed=view.create_leaderboard_embed(),
            view=view,
            ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send("❌ Fehler beim Laden der Bestenliste!", ephemeral=True)
            print(f"Leaderboard Error: {str(e)}")
            
    async def show_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="❓ Wordle-Hilfe",
            description=(
                "🌟 **Spielregeln:**\n"
                "1. Errate das 5-Buchstaben-Wort in 6 Versuchen\n"
                "2. Farben zeigen Treffergenauigkeit:\n"
                "   🟩 = Richtiger Buchstabe an richtiger Position\n"
                "   🟨 = Buchstabe im Wort, aber falsche Position\n"
                "   ⬛ = Buchstabe nicht im Wort\n\n"
                "💡 **Tipps:**\n"
                "- Nutze maximal 3 Tipps pro Spiel\n"
                "- Vergleiche dich mit anderen über die Ranglisten"
            ),
            color=discord.Color.blue()
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="search", description="Suche nach Benutzerstatistiken")
    async def search_stats(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SearchModal(self))
    
    @app_commands.command(name="settings", description="Privatsphäre-Einstellungen")
    async def user_settings_command(self, interaction: discord.Interaction):
        await self.open_settings(interaction)
    
    async def open_settings(self, interaction: discord.Interaction):
        view = SettingsView(self, interaction.user.id)
        if interaction.response.is_done():
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⚙️ Einstellungen",
                    description="Wähle deine Privatsphäre-Einstellungen:",
                    color=discord.Color.blue()
                ),
                view=view,
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⚙️ Einstellungen",
                    description="Wähle deine Privatsphäre-Einstellungen:",
                    color=discord.Color.blue()
                ),
                view=view,
                ephemeral=True
            )
    async def show_own_stats(self, interaction: discord.Interaction):
        """Zeigt die eigenen Statistiken an"""
        await self.show_stats(interaction, interaction.user)  

    async def show_stats(self, interaction: discord.Interaction, user: discord.User):
        """Hauptmethode für Statistiken"""
        try:
            is_own = interaction.user.id == user.id
            settings = self.settings.get_settings(user.id)
            
            if not is_own and not settings["stats_public"]:
                await interaction.response.send_message("❌ Diese Statistiken sind privat!", ephemeral=True)
                return
            
            public_games = [g for g in self.history.get_user_games(user.id, "global") if not g.get("anonymous", False)]
            anon_games = self.history.get_anonymous_games(settings["anon_id"])
            
            embed = discord.Embed(title="📊 Statistiken", color=discord.Color.gold())
            
            if public_games or anon_games:
                if public_games:
                    embed.add_field(
                        name="Öffentliche Spiele",
                        value=f"✅ {sum(g['won'] for g in public_games)} Siege\n"
                              f"❌ {len(public_games)-sum(g['won'] for g in public_games)} Niederlagen\n"
                              f"📊 {sum(g['won'] for g in public_games)/len(public_games)*100:.1f}% Winrate",
                        inline=True
                    )
                
                if anon_games:
                    embed.add_field(
                        name="🎭 Anonyme Spiele",
                        value=f"✅ {sum(g['won'] for g in anon_games)} Siege\n"
                              f"❌ {len(anon_games)-sum(g['won'] for g in anon_games)} Niederlagen\n"
                              f"📊 {sum(g['won'] for g in anon_games)/len(anon_games)*100:.1f}% Winrate",
                        inline=True
                    )
            else:
                embed.description = "📭 Noch keine Spiele gespielt!"
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ Fehler beim Laden der Statistiken!", ephemeral=True)
            print(f"Stats Error: {str(e)}")

        def get_daily_rank(self, user_id: int):
            leaderboard = self.daily_challenge.get_leaderboard()
            user_str = str(user_id)
            return next((i+1 for i, (u_id, _) in enumerate(leaderboard) if u_id == user_str), None)

    @app_commands.command(name="achievements", description="Zeige deine Achievements")
    async def _show_achievements(self, interaction: discord.Interaction):
        user_achievements = self.history.data["achievements"].get(str(interaction.user.id), {})
    
        embed = discord.Embed(
        title=f"🏆 Achievements - {interaction.user.display_name}",
        color=discord.Color.gold()
        )
    
        for achievement_id, data in self.achievement_system.ACHIEVEMENTS.items():
            status = "✅ " + datetime.fromisoformat(user_achievements[achievement_id]).strftime("%d.%m.%Y") if achievement_id in user_achievements else "❌"
            embed.add_field(
            name=f"{data['name']} {status}",
            value=data['description'],
            inline=False
            )
    
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="dailylb", description="Daily Challenge Bestenliste")
    async def daily_leaderboard(self, interaction: discord.Interaction):
        leaderboard = self.daily_challenge.get_leaderboard()[:10]
        
        embed = discord.Embed(
            title="🏆 Daily Challenge Leaderboard",
            description=f"Wort des Tages: ||{self.daily_challenge.current_word.upper()}||",
            color=discord.Color.blurple()
        )
        
        for i, (user_id, data) in enumerate(leaderboard):
            user = await self.bot.fetch_user(int(user_id))
            embed.add_field(
                name=f"{i+1}. {user.display_name}",
                value=f"Versuche: {data['attempts']} | Zeit: {datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S')}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

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