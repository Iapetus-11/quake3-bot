from discord.ext import commands

from bot.utils.code import execute_code, format_exception
from bot.quake3_bot import Quake3Bot


class OwnerCommands(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

    @commands.command(name="eval")
    @commands.is_owner()
    async def eval_stuff(self, ctx: commands.Context, *, stuff: str):
        stuff = stuff.strip(" `\n")

        if stuff.startswith("py"):
            stuff = stuff[2:]

        try:
            result = await execute_code(
                stuff, {"bot": self.bot, "http": self.bot.aiohttp_client}
            )

            result_str = f"{result}".replace("```", "｀｀｀")
            await ctx.reply(f"```\n{result_str}```")
        except Exception as e:
            await ctx.reply(f"```py\n{format_exception(e)[:2000-9].replace('```', '｀｀｀')}```")


async def setup(bot: Quake3Bot):
    await bot.add_cog(OwnerCommands(bot))
