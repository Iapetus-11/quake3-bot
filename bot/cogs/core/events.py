import sys

import arrow
from discord.ext import commands

from bot.quake3_bot import Quake3Bot
from bot.utils.code import format_exception


class Events(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

    async def on_event_error(
        self, event, *args, **kwargs
    ):  # logs errors in events, such as on_message
        exception = sys.exc_info()[1]
        traceback = format_exception(exception).replace("```", "｀｀｀")

        event_call_repr = f"{event}({',  '.join(list(map(repr, args)) + [f'{k}={repr(v)}' for k, v in kwargs.items()])})"
        self.bot.logger.error(
            f"An exception occurred in this event call:\n{event_call_repr}", exc_info=True
        )

        await self.bot.wait_until_ready()

        error_channel = await self.bot.get_error_channel()
        await error_channel.send(f"```py\n{event_call_repr[:100]}``````py\n{traceback[:1880]}```")

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


async def setup(bot: Quake3Bot):
    await bot.add_cog(Events(bot))
