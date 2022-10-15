from discord.ext import commands
from discord import app_commands
import discord

from bot.my_bot import MyBot


class HelloCommands(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot

    @commands.command(name="hello")
    async def hello_command(self, ctx: commands.Context):
        await ctx.reply(f"Hello {ctx.author.mention}!")

    @app_commands.command(name="hello")
    async def hello_slash_command(self, inter: discord.Interaction):
        await inter.response.send_message(f"Hello {inter.user.mention}!")


async def setup(bot: MyBot):
    await bot.add_cog(HelloCommands(bot))
