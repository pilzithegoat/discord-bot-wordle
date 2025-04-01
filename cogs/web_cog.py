from discord.ext import commands
import sqlite3

class WebConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def get_server_words(self, guild_id):
        conn = sqlite3.connect('wordle.db')
        c = conn.cursor()
        c.execute("SELECT words FROM server_config WHERE guild_id = ?", (guild_id,))
        result = c.fetchone()
        return result[0].split(',') if result else None
    
    def get_wordle_channel(self, guild_id):
        conn = sqlite3.connect('wordle.db')
        c = conn.cursor()
        c.execute("SELECT channel_id FROM server_config WHERE guild_id = ?", (guild_id,))
        result = c.fetchone()
        return result[0] if result else None

async def setup(bot):
    await bot.add_cog(WebConfig(bot))