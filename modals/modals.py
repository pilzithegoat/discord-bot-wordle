import discord
from discord.ui import Modal, TextInput
from models.game_history import GameHistory

class AnonCheckModal(Modal, title="🔒 Anonyme Spiele - Passwortprüfung"):
    password = TextInput(label="Passwort", placeholder="Dein Anonym-Passwort...", style=discord.TextStyle.short)
    
    def __init__(self, cog, user_id: int):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.verified = False

    async def on_submit(self, interaction: discord.Interaction):
        settings = self.cog.settings.get_settings(self.user_id)
        self.verified = verify_password(settings["anon_password"], self.password.value)
        await interaction.response.defer()

class PageSelectModal(Modal, title="🔢 Direkt zur Seite springen"):
    page_input = TextInput(label="Seitennummer", placeholder="Gib eine Zahl zwischen 1 und ... ein", required=True)
    
    def __init__(self, max_pages: int):
        super().__init__()
        self.page_number = None
        self.max_pages = max_pages
        self.page_input.placeholder = f"1 - {max_pages}"

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page = int(self.page_input.value)
            if 1 <= page <= self.max_pages:
                self.page_number = page
                await interaction.response.defer()
            else:
                await interaction.response.send_message(
                    f"❌ Ungültige Seite! Bitte zwischen 1 und {self.max_pages} wählen.",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message("❌ Bitte eine gültige Zahl eingeben!", ephemeral=True)


class GuessModal(Modal, title="Wort eingeben"):
    guess = TextInput(label="Dein 5-Buchstaben-Wort", min_length=5, max_length=5, custom_id="guess_input")
    
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_process_guess(interaction, self.guess.value)


class SearchModal(Modal, title="Benutzer suchen"):
    name = TextInput(label="Benutzername oder ID", custom_id="search_input")
    
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await commands.UserConverter().convert(interaction, self.name.value)
            await self.cog.show_stats(interaction, user)
        except commands.UserNotFound:
            await interaction.response.send_message("❌ Benutzer nicht gefunden!", ephemeral=True)
