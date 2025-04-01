import discord
from discord.ui import View, Button, Select, Modal, TextInput
from discord import Interaction, Embed, ui
from datetime import datetime

class StatsView(View):
    def __init__(self, cog, user: discord.User):
        super().__init__(timeout=120)
        self.cog = cog
        self.user = user
        self.page = 0
        self.page_size = 5
        self.games = self.load_games()
        self.total_pages = max(1, (len(self.games) - 1) // self.page_size + 1)

    def load_games(self):
        public_games = self.cog.history.get_user_games(self.user.id, "global")
        anon_games = self.cog.history.get_anonymous_games(
            self.cog.settings.get_settings(self.user.id)["anon_id"]
        )
        return public_games + anon_games

    def create_embed(self):
        embed = discord.Embed(title=f"📊 Statistiken für {self.user.display_name}", color=discord.Color.gold())
        
        for game in self.paginated_games():
            status = "🟢" if game["won"] else "🔴"
            embed.add_field(
                name=f"{status} Spiel {game['id']}",
                value=(
                    f"🔑 Wort: ||{game['word'].upper()}||\n"
                    f"📅 {datetime.fromisoformat(game['timestamp']).strftime('%d.%m.%Y %H:%M')}\n"
                    f"💡 Tipps: {game['hints']} | ⏱️ {game['duration']:.1f}s"
                ),
                inline=False
            )

        embed.set_footer(text=f"Seite {self.page + 1}/{self.total_pages}")
        return embed

    @ui.button(emoji="⬅️", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.page = max(0, self.page - 1)
        await self.update(interaction)

    @ui.button(emoji="➡️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.page = min(self.total_pages - 1, self.page + 1)
        await self.update(interaction)

    @ui.button(emoji="🔍", style=discord.ButtonStyle.secondary, label="Nach ID suchen")
    async def search_id(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SearchIDModal(self.cog, self.user))

    async def update(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, Button):
                if child.emoji.name == "⬅️":
                    child.disabled = self.page == 0
                elif child.emoji.name == "➡️":
                    child.disabled = self.page >= self.total_pages - 1
        
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class SearchIDModal(Modal, title="🔍 Spiel nach ID suchen"):
    game_id = TextInput(label="Spiel-ID", placeholder="Gib die 8-stellige ID ein", min_length=8, max_length=8)

    def __init__(self, cog, user: discord.User):
        super().__init__()
        self.cog = cog
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        game = self.find_game(self.game_id.value.upper())
        if game:
            embed = discord.Embed(title=f"🔍 Spiel {self.game_id.value}", color=discord.Color.blue())
            embed.add_field(name="Wort", value=f"||{game['word'].upper()}||")
            embed.add_field(name="Ergebnis", value="Gewonnen 🏆" if game['won'] else "Verloren 💥")
            embed.add_field(name="Datum", value=datetime.fromisoformat(game['timestamp']).strftime('%d.%m.%Y %H:%M'))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Kein Spiel mit dieser ID gefunden!", ephemeral=True)

    def find_game(self, game_id: str):
        games = self.cog.history.data["global"]["users"].get(str(self.user.id), [])
        anon_games = self.cog.history.get_anonymous_games(
            self.cog.settings.get_settings(self.user.id)["anon_id"]
        )
        return next((g for g in games + anon_games if g["id"] == game_id), None)
