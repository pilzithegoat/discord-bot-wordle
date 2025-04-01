import discord
from discord import ui
from discord.ui import View, Button, Select, Modal, TextInput, button
from modals.modals import GuessModal
from typing import Optional

MAX_HINTS = 3
WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"

class EndGameView(View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=10)
        self.cog = cog
        self.user_id = user_id
    
    @ui.button(label="Neues Spiel", style=discord.ButtonStyle.green, emoji="🔄", custom_id="new_game")
    async def new_game(self, interaction: discord.Interaction, button: Button):
        await self.cog.start_new_game(interaction)
    
    @ui.button(label="Statistiken", style=discord.ButtonStyle.blurple, emoji="📊", custom_id="end_stats")
    async def show_stats(self, interaction: discord.Interaction, button: Button):
        user = await self.cog.bot.fetch_user(self.user_id)
        await self.cog.show_stats(interaction, user)

class MainMenu(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
        self.add_item(Button(
            label="Neues Spiel", 
            style=discord.ButtonStyle.green, 
            emoji="🎮",
            custom_id="persistent_new_game"
        ))

        self.add_item(Button(
            label="Daily Challenge",
            style=discord.ButtonStyle.blurple,
            emoji="🌞",
            custom_id="persistent_daily"
        ))
        
        options = [
            discord.SelectOption(label="Daily Challenge", value="daily", emoji="🌞"),
            discord.SelectOption(label="Achievements", value="achievements", emoji="🏆"),
            discord.SelectOption(label="Leaderboard", value="leaderboard", emoji="🏆"),
            discord.SelectOption(label="Statistiken", value="stats", emoji="📊"),
            discord.SelectOption(label="Historie", value="history", emoji="📜"),
            discord.SelectOption(label="Einstellungen", value="settings", emoji="⚙️"),
            discord.SelectOption(label="Hilfe", value="help", emoji="❓")
        ]
        self.select = Select(
            placeholder="🏅 Wordle-Menü",
            options=options,
            custom_id="persistent_main_menu"
        )
        self.select.callback = self.menu_select
        self.add_item(self.select)

    async def new_game_callback(self, interaction: discord.Interaction):
        await self.cog.start_new_game(interaction)

# In der MainMenu-Klasse:
    async def menu_select(self, interaction: discord.Interaction):
        choice = interaction.data["values"][0]
        handlers = {
        "daily": self.cog.handle_daily,
        "achievements": self.cog._show_achievements,
        "leaderboard": self.cog.show_leaderboard,
        "stats": self.cog.show_own_stats,
        "history": self.cog.show_own_history,
        "settings": self.cog.open_settings,
        "help": self.cog.show_help
        }
        handler = handlers.get(choice)
        if handler:
            await handler(interaction)  # 👈 Korrekter Methodenaufruf
        else:
            await interaction.response.send_message("❌ Ungültige Auswahl!", ephemeral=True)

    async def show_daily_options(self, interaction: discord.Interaction):
        """Zeigt Daily-Challenge-Optionen an"""
        view = DailyChallengeView(self.cog)
        embed = discord.Embed(
        title="🌞 Daily Challenges",
        description="Wähle eine Option:",
        color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "persistent_new_game":
            await self.cog.start_new_game(interaction)
            return False
        return True

class GameView(View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.user_id = user_id
        self.update_buttons()
    
    def update_buttons(self):
        self.clear_items()
        game = self.cog.games.get(self.user_id)
        
        self.add_item(Button(
            label="Raten ✏️", 
            style=discord.ButtonStyle.primary, 
            emoji="📝",
            custom_id="guess_button"
        ))
        self.add_item(Button(
            label=f"Tipp 💡 ({game.hints_used if game else 0}/{MAX_HINTS})",
            style=discord.ButtonStyle.secondary,
            disabled=(not game or game.hints_used >= MAX_HINTS),
            emoji="💡",
            custom_id="hint_button"
        ))
        self.add_item(Button(
            label="Beenden 🗑️", 
            style=discord.ButtonStyle.danger, 
            emoji="❌",
            custom_id="quit_button"
        ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ Nicht dein Spiel!", ephemeral=True)
                return False
        
            custom_id = interaction.data["custom_id"]
        
            if custom_id == "guess_button":
                await interaction.response.send_modal(GuessModal(self.cog))
            elif custom_id == "hint_button":
                await self.cog.handle_give_hint(interaction)
            elif custom_id == "quit_button":
                await self.cog.handle_end_game(interaction, False)
            
            return False
        except Exception as e:
            if not interaction.response.is_done():  # 👈 Prüfen ob bereits geantwortet wurde
                await interaction.response.send_message(
                    "⚠️ Ein Fehler ist aufgetreten! Bitte versuche es erneut.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(  # 👈 followup verwenden
                    "⚠️ Ein Fehler ist aufgetreten!",
                    ephemeral=True
                )
            print(f"Interaktionsfehler: {str(e)}")
