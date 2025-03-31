import discord
import uuid
from discord import View, Button, Select, Modal
from models.game_history import GameHistory
from modals.modals import PageSelectModal, AnonCheckModal
from dotenv import load_dotenv

class InitialHistoryView(View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        
        self.add_item(Button(
            label="Meine Historie", 
            style=discord.ButtonStyle.primary, 
            custom_id="own_history"
        ))
        self.add_item(Button(
            label="Anderer Spieler", 
            style=discord.ButtonStyle.secondary, 
            custom_id="other_history"
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "own_history":
            await self.cog.show_own_history(interaction)
        else:
            await interaction.response.send_modal(SearchHistoryModal(self.cog))
        return False

class SearchHistoryModal(Modal, title="🎮 Spieler suchen"):
    username = TextInput(label="Benutzername oder ID", required=True)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await commands.UserConverter().convert(interaction, self.username.value)
            settings = self.cog.settings.get_settings(user.id)
            
            if not settings["history_public"]:
                await interaction.response.send_message("❌ Dieser Spieler hat seine Historie privat!", ephemeral=True)
                return
                
            await self.cog.show_history(interaction, user)
            
        except commands.UserNotFound:
            await interaction.response.send_message("❌ Spieler nicht gefunden!", ephemeral=True)


class HistoryView(View):
    def __init__(self, cog, user_id: int, guild_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id
        self.current_scope = "server"
        self.current_mode = "public"
        self.page = 0
        self.view_id = str(uuid.uuid4())[:8]

        # UI-Komponenten
        self.scope_select = Select(placeholder="🌐 Bereich wählen", options=[], custom_id=f"scope_{self.view_id}")
        self.mode_select = Select(placeholder="🎭 Modus wählen", options=[], custom_id=f"mode_{self.view_id}")
        self.update_selects()
        
        self.nav_buttons = [
            Button(emoji="⏮️", style=discord.ButtonStyle.grey, custom_id=f"first_{self.view_id}"),
            Button(emoji="⬅️", style=discord.ButtonStyle.primary, custom_id=f"prev_{self.view_id}"),
            Button(emoji="🔢", style=discord.ButtonStyle.secondary, custom_id=f"page_{self.view_id}"),
            Button(emoji="➡️", style=discord.ButtonStyle.primary, custom_id=f"next_{self.view_id}"),
            Button(emoji="⏭️", style=discord.ButtonStyle.grey, custom_id=f"last_{self.view_id}")
        ]
        
        # Komponenten hinzufügen
        self.scope_select.callback = self.update_scope
        self.mode_select.callback = self.update_mode
        self.add_item(self.scope_select)
        self.add_item(self.mode_select)
        
        for btn in self.nav_buttons:
            btn.callback = self.handle_navigation
            self.add_item(btn)

        self.update_button_states()

    def update_selects(self):
        self.scope_select.options = [
            discord.SelectOption(label="🏠 Server", value="server", default=self.current_scope == "server"),
            discord.SelectOption(label="🌍 Global", value="global", default=self.current_scope == "global")
        ]
        self.mode_select.options = [
            discord.SelectOption(label="🌍 Öffentlich", value="public", default=self.current_mode == "public"),
            discord.SelectOption(label="🎭 Anonym", value="anonymous", default=self.current_mode == "anonymous")
        ]

    def update_button_states(self):
        games = self.get_games()
        total = len(games)
        for btn in self.nav_buttons:
            if btn.emoji.name == "⏮️":
                btn.disabled = self.page <= 0 or total == 0
            elif btn.emoji.name == "⬅️":
                btn.disabled = self.page <= 0 or total == 0
            elif btn.emoji.name == "➡️":
                btn.disabled = self.page >= total - 1 or total == 0
            elif btn.emoji.name == "⏭️":
                btn.disabled = self.page >= total - 1 or total == 0

    async def handle_navigation(self, interaction: discord.Interaction):
        action = interaction.data["custom_id"].split("_")[0]
        games = self.get_games()
        total = len(games)

        if action == "page":
            modal = PageSelectModal(total)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.page_number:
                self.page = modal.page_number - 1
        else:
            if action == "first": self.page = 0
            elif action == "prev": self.page = max(0, self.page - 1)
            elif action == "next": self.page = min(total - 1, self.page + 1)
            elif action == "last": self.page = total - 1

        await self.safe_update(interaction)

    async def update_scope(self, interaction: discord.Interaction):
        self.current_scope = interaction.data["values"][0]
        self.page = 0
        await self.safe_update(interaction)

    async def update_mode(self, interaction: discord.Interaction):
        new_mode = interaction.data["values"][0]
        if new_mode == "anonymous":
            if not await self.verify_anonymity(interaction):
                return
        self.current_mode = new_mode
        self.page = 0
        await self.safe_update(interaction)

    async def verify_anonymity(self, interaction: discord.Interaction) -> bool:
        settings = self.cog.settings.get_settings(self.user_id)
        if not settings["anon_password"]:
            await interaction.response.send_message("❌ Kein Anonym-Passwort gesetzt!", ephemeral=True)
            return False
        modal = AnonCheckModal(self.cog, self.user_id)
        await interaction.response.send_modal(modal)
        await modal.wait()
        return modal.verified

    def get_games(self):
        if self.current_mode == "anonymous":
            settings = self.cog.settings.get_settings(self.user_id)
            return self.cog.history.get_anonymous_games(settings["anon_id"])
        return self.cog.history.get_user_games(
            self.user_id,
            self.current_scope,
            self.guild_id if self.current_scope == "server" else None
        )

    def create_embed(self):
        games = self.get_games()
        game = games[self.page] if games else None
        
        embed = discord.Embed(
            title=f"📜 {'Globale' if self.current_scope == 'global' else 'Server'} Historie",
            description=f"Modus: {'🎭 Anonym' if self.current_mode == 'anonymous' else '🌍 Öffentlich'}",
            color=discord.Color.blue()
        ).set_footer(text=f"Seite {self.page + 1}/{len(games)}")

        if game:
            # Server-Info für globale Spiele
            server_info = ""
            if self.current_scope == "global" and "guild_id" in game:
                guild = self.cog.bot.get_guild(game["guild_id"])
                server_info = f"\n🏰 Server: {guild.name if guild else 'Unbekannt'}"
            
            # Spielverlauf
            attempts = "\n".join(
                f"`{g['word'].upper()}`: {' '.join(g['result'])}" 
                for g in game["guesses"]
            )
            
            embed.add_field(
                name="🔍 Spiel-Details",
                value=(
                    f"🔑 ID: `{game['id']}`{server_info}\n"
                    f"📅 {datetime.fromisoformat(game['timestamp']).strftime('%d.%m.%Y %H:%M')}\n"
                    f"🏆 {'Gewonnen' if game['won'] else 'Verloren'} in {game['attempts']} Versuchen\n"
                    f"💡 {game['hints']} Tipps | ⏱️ {game['duration']:.1f}s"
                ),
                inline=False
            )
            
            if attempts:
                embed.add_field(name="📈 Versuchsverlauf", value=attempts, inline=False)
            
            embed.set_thumbnail(url="https://emojicdn.elk.sh/🎭" if game.get("anonymous") else "https://emojicdn.elk.sh/🌍")

        return embed

    async def safe_update(self, interaction: discord.Interaction):
        self.update_selects()
        self.update_button_states()
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=self.create_embed(), view=self)
            else:
                await interaction.response.edit_message(embed=self.create_embed(), view=self)
        except Exception as e:
            print(f"Update Error: {e}")

    async def update_display(self, interaction: discord.Interaction):
        """Veraltet, wird durch safe_update ersetzt"""
        await self.safe_update(interaction)

class HistorySelectionView(View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        
        self.add_item(Button(
            label="Meine Historie", 
            style=discord.ButtonStyle.primary, 
            custom_id="own_history"
        ))
        self.add_item(Button(
            label="Anderer Spieler", 
            style=discord.ButtonStyle.secondary, 
            custom_id="other_history"
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "own_history":
            await self.cog.show_user_history(interaction, interaction.user)
        else:
            await interaction.response.send_modal(HistorySearchModal(self.cog))
        return False

class HistorySearchModal(Modal, title="🔍 Spieler suchen"):
    username = TextInput(label="Benutzername oder ID", required=True)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await commands.UserConverter().convert(interaction, self.username.value)
            await self.cog.show_user_history(interaction, user)
        except commands.UserNotFound:
            await interaction.response.send_message("❌ Spieler nicht gefunden!", ephemeral=True)
