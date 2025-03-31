import discord
from discord.ui import View, Button
from discord import Interaction, Embed

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
