import discord
from discord.ext import commands
from discord import app_commands as slash_commands

from bot.quake3_bot import Quake3Bot


class HelpCommands(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

    @slash_commands.command(name="help", description="Get helpful information about Quake III Bot")
    async def help(self, inter: discord.Interaction):
        embed = self.bot.default_embed()

        embed.title = "Quake III Bot Commands"

        embed.description = "\n\n".join(
            [
                f"**`/{cmd.qualified_name} {' '.join(f'<{p.display_name}>' for p in cmd.parameters)}".strip()
                + f"`** *{cmd.description}*"
                for cmd in self.bot.tree.walk_commands()
            ]
        )

        await inter.response.send_message(embed=embed)


async def setup(bot: Quake3Bot):
    await bot.add_cog(HelpCommands(bot))
