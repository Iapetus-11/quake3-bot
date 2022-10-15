import arrow
from discord.ext import commands

from bot.my_bot import MyBot
from bot.utils.code import format_exception


class Events(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Bot is connected and ready!")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CommandOnCooldown):
            retry_after_in = (
                arrow.now().shift(seconds=error.retry_after).humanize(only_distance=True)
            )
            await ctx.reply(f"Cool down! You can use this command again in {retry_after_in}")
        elif isinstance(error, commands.NotOwner):
            await ctx.reply("This command is only available to the bot owners!")
        else:
            error_formatted = format_exception(error)

            self.bot.logger.error(error_formatted)

            debug_info = (
                f"```\n{ctx.author} ({ctx.author.id}): {ctx.message.content}"[:200]
                + f"``````py\n{error_formatted.replace('```', '｀｀｀')}"[: 2000 - 209]
                + "```"
            )

            await ctx.send(debug_info)


async def setup(bot: MyBot):
    await bot.add_cog(Events(bot))
