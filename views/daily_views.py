import discord
import os
from dotenv import load_dotenv
from discord.ui import View, Button, Select, Modal, TextInput
from discord import Interaction, Embed
from discord.ext import commands

## Worde Variablen non used yet. When use one do a # behind the variable
load_dotenv()
MAX_HINTS = int(os.getenv("MAX_HINTS", 0))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 0))
WORDS_FILE = os.getenv("WORDS_FILE")
DATA_FILE = os.getenv("DATA_FILE")
CONFIG_FILE = os.getenv("CONFIG_FILE")
SETTINGS_FILE = os.getenv("SETTINGS_FILE")
DAILY_FILE = os.getenv("DAILY_FILE")

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
