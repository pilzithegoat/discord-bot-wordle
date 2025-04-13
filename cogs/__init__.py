from .wordle_cog import WordleCog

async def setup(bot):
    cog = WordleCog(bot)
    await cog.setup()
    await bot.add_cog(cog)
