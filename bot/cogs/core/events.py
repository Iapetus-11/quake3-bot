import time
import traceback

import arrow
import discord
import discord.app_commands as slash_commands
from discord.ext import commands

from bot.models import DiscordGuild, DiscordUser
from bot.models.command_execution import CommandExecution
from bot.quake3_bot import Quake3Bot
from bot.utils.code import format_exception
from bot.utils.text import text_to_discord_file


class Events(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

        # Register event listeners
        bot.event(self.on_event_error)
        bot.tree.on_error = self.on_slash_command_error

    async def on_event_error(
        self, event, *args, **kwargs
    ):  # logs errors in events, such as on_message
        event_call_repr = f"{event}({',  '.join(list(map(repr, args)) + [f'{k}={repr(v)}' for k, v in kwargs.items()])})"
        self.bot.logger.error(
            f"An exception occurred in this event call:\n{event_call_repr}", exc_info=True
        )

        await self.bot.wait_until_ready()

        error_channel = await self.bot.get_error_channel()
        await error_channel.send(
            f"```py\n{event_call_repr[:1920]}```",
            file=text_to_discord_file(
                traceback.format_exc(),
                file_name=f"error_tb_ev_{time.time():0.0f}.txt",
            ),
        )

    async def on_slash_command_error(self, inter: discord.Interaction, error: Exception):
        self.bot.logger.error(
            f"An exception occurred in the /{inter.command} command", exc_info=True
        )

        cmd_call_repr = f"```\n{inter.user} (user_id={inter.user.id}) (guild_id={inter.guild_id}): {inter.message}```"

        error_channel = await self.bot.get_error_channel()
        await error_channel.send(
            cmd_call_repr,
            file=text_to_discord_file(
                format_exception(error, None),
                file_name=f"error_tb_cmd_{time.time():0.0f}.txt",
            ),
        )

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

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        inter: discord.Interaction,
        command: slash_commands.Command | slash_commands.ContextMenu,
    ):
        if not isinstance(command, slash_commands.Command):
            return

        discord_user, discord_guild = await self.bot.get_inter_db_data(inter)

        await CommandExecution.create(
            name=command.qualified_name,
            discord_user=discord_user,
            discord_guild=discord_guild,
            discord_channel_id=inter.channel_id,
        )


async def setup(bot: Quake3Bot):
    await bot.add_cog(Events(bot))
