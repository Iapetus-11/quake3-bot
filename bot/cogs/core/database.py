from discord.ext import commands

from bot.my_bot import MyBot


class Database(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot


async def setup(bot: MyBot):
    await bot.add_cog(Database(bot))
