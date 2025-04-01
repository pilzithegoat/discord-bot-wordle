import discord
from discord.ui import View, Button, Modal, TextInput, Select
from discord import Interaction
from utils.helpers import verify_password

class SettingsView(View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.settings = cog.settings.get_settings(user_id)
        self.add_buttons()
    
    def add_buttons(self):
        buttons = [
            ("stats_public", "📊 Stats", 0),
            ("history_public", "📜 Historie", 0),
            ("anonymous", "🎭 Anonym", 1),
            ("anon_password", "🔑 Passwort", 2)
        ]
        
        for setting, label, row in buttons:
            btn = Button(
                label=f"{label} {'✅' if self.settings[setting] else '❌'}" if setting != "anon_password" else "🔑 Passwort setzen",
                style=discord.ButtonStyle.primary,
                row=row,
                emoji="⚙️" if setting != "anon_password" else "🔒",
                custom_id=f"setting_{setting}"
            )
            btn.callback = lambda i, s=setting: self.toggle_setting(i, s)
            self.add_item(btn)
    
    async def toggle_setting(self, interaction: discord.Interaction, setting: str):
        if setting == "anon_password":
            await interaction.response.send_modal(AnonPasswordSetModal(self.cog, self.user_id))
            return
        
        new_value = not self.settings[setting]
        self.cog.settings.update_settings(self.user_id, **{setting: new_value})
        await interaction.response.edit_message(view=SettingsView(self.cog, self.user_id))

class AnonPasswordSetModal(Modal, title="Anonym-Passwort setzen"):
    password = TextInput(label="Neues Passwort", placeholder="Mindestens 8 Zeichen", required=True, min_length=8)
    
    def __init__(self, cog, user_id: int):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
    
    async def on_submit(self, interaction: discord.Interaction):
        self.cog.settings.update_settings(self.user_id, anon_password=self.password.value)
        await interaction.response.send_message("✅ Passwort erfolgreich gesetzt!", ephemeral=True)

class AnonPasswordModal(Modal, title="Anonyme Spiele Passwort"):
    password = TextInput(label="Passwort", placeholder="Gib dein Anonym-Passwort ein", required=True)
    
    def __init__(self, cog, user_id: int, parent_view: View):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.parent_view = parent_view
    
    async def on_submit(self, interaction: discord.Interaction):
        settings = self.cog.settings.get_settings(self.user_id)
        if verify_password(settings["anon_password"], self.password.value):
            if hasattr(self.parent_view, 'anon_mode'):
                self.parent_view.anon_mode = True
                self.parent_view.page = 0
                self.parent_view.update_buttons()
                await interaction.response.edit_message(embed=self.parent_view.create_embed(), view=self.parent_view)
            else:
                view = HistoryView(self.cog, self.user_id, interaction.guild.id)
                await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Falsches Passwort!", ephemeral=True)

