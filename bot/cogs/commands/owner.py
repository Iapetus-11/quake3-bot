from discord.ext import commands

from bot.utils.code import execute_code, format_exception
from bot.my_bot import MyBot
from bot.cogs.core.database import Database


class OwnerCommands(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @property
    def db(self) -> Database:
        return self.bot.get_cog("Database")

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_stuff(self, ctx: commands.Context, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        try:
            result = await execute_code(
                stuff, {"bot": self.bot, "db": self.db, "http": self.bot.aiohttp_client}
            )

            result_str = f"{result}".replace("```", "｀｀｀")
            await ctx.reply(f"```\n{result_str}```")
        except Exception as e:
            await ctx.reply(f"```py\n{format_exception(e)[:2000-9].replace('```', '｀｀｀')}```")


async def setup(bot: MyBot):
    await bot.add_cog(OwnerCommands(bot))
