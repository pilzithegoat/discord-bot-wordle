import discord
from discord.ui import View, Button, Select, Modal, TextInput
from discord import Interaction, Embed
from discord.ext import commands


WORDS_FILE = "words.txt"
MAX_ATTEMPTS = 6
MAX_HINTS = 3
DATA_FILE = "wordle_data.json"
CONFIG_FILE = "server_config.json"
SETTINGS_FILE = "user_settings.json"
DAILY_FILE = "daily_data.json"
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class DailyChallengeView(View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        
        self.add_item(Button(
            label="Heutige Challenge starten", 
            style=discord.ButtonStyle.green, 
            emoji="🎮",
            custom_id="daily_start"
        ))
        
        self.add_item(Button(
            label="Leaderboard anzeigen", 
            style=discord.ButtonStyle.blurple, 
            emoji="🏆",
            custom_id="daily_leaderboard"
        ))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "daily_start":
            await self.cog.daily_command(interaction)
        elif interaction.data["custom_id"] == "daily_leaderboard":
            await self.cog.daily_leaderboard(interaction)
        return False
    
    @bot.tree.command(name="daily_leaderboard", description="Zeigt das Daily-Challenge-Ranking")
    async def daily_leaderboard(self, interaction: discord.Interaction):
        leaderboard = self.daily_challenge.get_leaderboard()[:10]
    
        embed = discord.Embed(
        title="🏆 Daily Leaderboard",
        color=discord.Color.gold()
        )
    
        for idx, (user_id, data) in enumerate(leaderboard, 1):
            user = await self.bot.fetch_user(int(user_id))
            embed.add_field(
            name=f"{idx}. {user.display_name}",
            value=f"Versuche: {data['attempts']} | Zeit: {data['timestamp']}",
            inline=False
            )
    
        await interaction.response.send_message(embed=embed)
