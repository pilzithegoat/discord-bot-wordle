import discord
import uuid
import os
from discord.ui import View, Button, Select, Modal, TextInput
from models.game_history import GameHistory
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime
from utils.helpers import get_scope_label

## Worde Variablen. When use one do a # behind the variable and write # - used
load_dotenv()
MAX_HINTS = int(os.getenv("MAX_HINTS", 0))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 0)) # - used
WORDS_FILE = os.getenv("WORDS_FILE")
DATA_FILE = os.getenv("DATA_FILE")
CONFIG_FILE = os.getenv("CONFIG_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
DAILY_FILE = os.getenv("DAILY_FILE")

class EnhancedLeaderboardView(View):
    def __init__(self, cog, interaction: discord.Interaction, guild_id: Optional[int], scope: str = "server"):
        super().__init__(timeout=60)
        self.cog = cog
        self.interaction = interaction  # Speichere die Interaktion
        self.guild_id = guild_id
        self.scope = scope
        self.leaderboard_data = []
        self.current_page = 0
        self.page_size = 10
        self.view_id = str(uuid.uuid4())[:8]
        self.initialize_data()
        self.create_components()

    def initialize_data(self):
        raw_data = self.cog.history.get_leaderboard(self.scope, self.guild_id)
        self.leaderboard_data = sorted(
            [entry for entry in raw_data if entry['total'] > 0],
            key=lambda x: (-x['wins'], -x['total'], x['avg_attempts']),
            reverse=False
        )[:100]

    def create_components(self):
        self.clear_items()
        
        # Scope Buttons
        server_btn = Button(
            emoji="🏠",
            label="Server",
            style=discord.ButtonStyle.primary if self.scope == "server" else discord.ButtonStyle.secondary,
            custom_id=f"scope_server_{self.view_id}"
        )
        server_btn.callback = self.switch_scope_server
        self.add_item(server_btn)

        global_btn = Button(
            emoji="🌍",
            label="Global",
            style=discord.ButtonStyle.primary if self.scope == "global" else discord.ButtonStyle.secondary,
            custom_id=f"scope_global_{self.view_id}"
        )
        global_btn.callback = self.switch_scope_global
        self.add_item(global_btn)

        # Pagination
        if len(self.leaderboard_data) > self.page_size:
            prev_btn = Button(emoji="⬅️", custom_id=f"prev_page_{self.view_id}")
            prev_btn.callback = self.prev_page
            self.add_item(prev_btn)

            next_btn = Button(emoji="➡️", custom_id=f"next_page_{self.view_id}")
            next_btn.callback = self.next_page
            self.add_item(next_btn)

        # Zusätzliche Buttons
        stats_btn = Button(
            emoji="📊",
            label="Server Stats",
            style=discord.ButtonStyle.secondary,
            custom_id=f"show_stats_{self.view_id}"
        )
        stats_btn.callback = self.show_server_stats
        self.add_item(stats_btn)
        
        recent_btn = Button(
            emoji="🕒",
            label="Letzte Spiele",
            style=discord.ButtonStyle.secondary,
            custom_id=f"show_recent_{self.view_id}"
        )
        recent_btn.callback = self.show_recent_games
        self.add_item(recent_btn)

    def create_leaderboard_embed(self):
        embed = discord.Embed(
            title=f"🏆 {get_scope_label(self.scope)} Rangliste",
            color=discord.Color.gold()
        )
        
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_data = self.leaderboard_data[start_idx:end_idx]

        # Korrektur: Verwende self.interaction statt self.cog.ctx
        user_position = next(
            (i+1 for i, entry in enumerate(self.leaderboard_data) 
            if entry["user_id"] == self.interaction.user.id  # 👈 Korrigierte Zeile
        ), None)

        if user_position:
            embed.description = f"Deine Position: #{user_position}"

        for idx, entry in enumerate(page_data, start=1):
            user = self.cog.bot.get_user(entry['user_id'])
            if not user:
                continue
                
            stats = [
                f"🏆 Siege: {entry['wins']}",
                f"📊 Winrate: {entry['win_rate']*100:.1f}%",
                f"🔢 Ø Versuche: {entry['avg_attempts']:.1f}"
            ]
            
            embed.add_field(
                name=f"{start_idx + idx}. {user.display_name}",
                value="\n".join(stats),
                inline=False
            )

        embed.set_footer(text=f"Seite {self.current_page + 1}/{(len(self.leaderboard_data)-1)//self.page_size + 1}")
        return embed

    async def update_view(self, interaction: discord.Interaction):
        self.create_components()
        try:
            await interaction.response.edit_message(
                embed=self.create_leaderboard_embed(),
                view=self
            )
        except discord.NotFound:
            await interaction.followup.send("❌ Leaderboard konnte nicht aktualisiert werden!", ephemeral=True)

    async def switch_scope_server(self, interaction: discord.Interaction):
        self.scope = "server"
        self.guild_id = interaction.guild.id
        self.current_page = 0
        self.initialize_data()
        await self.update_view(interaction)

    async def switch_scope_global(self, interaction: discord.Interaction):
        self.scope = "global"
        self.guild_id = None
        self.current_page = 0
        self.initialize_data()
        await self.update_view(interaction)

    async def prev_page(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        max_page = (len(self.leaderboard_data) - 1) // self.page_size
        self.current_page = min(max_page, self.current_page + 1)
        await self.update_view(interaction)

    async def show_own_stats(self, interaction: discord.Interaction):
        await self.cog.show_own_stats(interaction)

    async def show_own_games(self, interaction: discord.Interaction):
        view = RecentGamesView(
            cog=self.cog,
            user_id=interaction.user.id,
            public_games=[]
        )
        await interaction.response.send_message(
            embed=view.create_embed(),
            view=view,
            ephemeral=True
        )

    async def show_server_stats(self, interaction: discord.Interaction):
        """Zeigt Server-Statistiken für alle sichtbar"""
        try:
            leaderboard = self.cog.history.get_leaderboard("server", self.guild_id)
            total_games = sum(entry['total'] for entry in leaderboard)
            total_wins = sum(entry['wins'] for entry in leaderboard)
            
            embed = discord.Embed(
                title=f"📊 {get_scope_label(self.scope)} Statistiken",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="Gesamtspiele",
                value=f"🕹️ {total_games}",
                inline=True
            )
            
            embed.add_field(
                name="Gewonnene Spiele",
                value=f"🏆 {total_wins}",
                inline=True
            )
            
            embed.add_field(
                name="Durchschnittliche Winrate",
                value=f"📊 {total_wins/total_games*100:.1f}%" if total_games > 0 else "📊 0%",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                "❌ Fehler beim Laden der Statistiken!",
                ephemeral=True
            )

    async def show_recent_games(self, interaction: discord.Interaction):
        """Zeigt die letzten Server-Spiele für alle sichtbar"""
        try:
            view = RecentGamesView(self.cog, interaction.guild.id)  # 👈 guild.id statt guild_id
            await interaction.response.send_message(
                embed=view.create_embed(),
                view=view,
                ephemeral=True
            )
        except Exception as e:
            print(f"Fehler: {str(e)}")
            await interaction.response.send_message(
                "❌ Fehler beim Laden der Spiele!",
                ephemeral=True
            )

class RecentGamesView(View):
    def __init__(self, cog, guild_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.guild_id = guild_id
        self.page = 0
        self.page_size = 5  # Reduzierte Anzahl für bessere Übersicht
        self.games = self.load_games()
        self.total_pages = max(1, (len(self.games) - 1) // self.page_size + 1)
        self.include_anonymous = False  # Neuer Filter

        prev_button = Button(emoji="⬅️", style=discord.ButtonStyle.primary)
        prev_button.callback = self.prev_page
        self.add_item(prev_button)

        next_button = Button(emoji="➡️", style=discord.ButtonStyle.primary)
        next_button.callback = self.next_page
        self.add_item(next_button)

    def load_games(self):
        all_games = []
        guild_data = self.cog.history.data["guilds"].get(str(self.guild_id), {})

        # Öffentliche Spiele
        for user_id_str, games in guild_data.get("users", {}).items():
            all_games.extend([
                ("public", int(user_id_str), game) 
                for game in games 
                if not game.get("anonymous", False)
            ])

        # Anonyme Spiele
        for anon_id in self.cog.history.data["anonymous_games"]:
            anon_games = self.cog.history.get_anonymous_games(anon_id)
            all_games.extend([
                ("anon", anon_id, game)
                for game in anon_games
                if game.get("guild_id") == self.guild_id
            ])

        return sorted(all_games, key=lambda x: x[2]["timestamp"], reverse=True)[:100]

    def create_embed(self):
        embed = discord.Embed(title="🕒 Letzte Server-Spiele", color=discord.Color.blue())
        
        start_idx = self.page * self.page_size
        for idx, (game_type, identifier, game) in enumerate(self.paginated_games(), start=1):
            global_number = start_idx + idx
            if game_type == "public":
                user = self.cog.bot.get_user(identifier)
                name = f"{user.display_name if user else 'Unbekannt'} (ID: {game['id']})"
            else:
                name = f"🎭 Anonym (ID: {game['id']})"

            embed.add_field(
                name=f"Spiel {global_number} - {name}",
                value=(
                    f"🏆 {'Gewonnen' if game['won'] else 'Verloren'}\n"
                    f"🔑 Wort: ||{game['word'].upper()}||\n"
                    f"📅 {datetime.fromisoformat(game['timestamp']).strftime('%d.%m.%Y %H:%M')}\n"
                    f"🔢 Versuche: {game['attempts']}/{MAX_ATTEMPTS}"
                ),
                inline=False
            )

        embed.set_footer(text=f"Seite {self.page + 1}/{self.total_pages}")
        return embed

    def paginated_games(self):
        start = self.page * self.page_size
        end = start + self.page_size
        return self.games[start:end]

    async def prev_page(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        await self.update_view(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.page = min(self.total_pages - 1, self.page + 1)
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        # Update Button-Status
        for child in self.children:
            if isinstance(child, Button):
                if child.emoji.name == "⬅️":
                    child.disabled = (self.page == 0)
                elif child.emoji.name == "➡️":
                    child.disabled = (self.page >= self.total_pages - 1)
        
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    def update_button_states(self):
        for child in self.children:
            if isinstance(child, Button):
                if child.emoji.name == "⬅️":
                    child.disabled = self.page == 0
                elif child.emoji.name == "➡️":
                    child.disabled = self.page >= self.total_pages - 1