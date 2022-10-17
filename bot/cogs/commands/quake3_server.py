import socket

import aioq3rcon
import discord
import validators
from discord import app_commands as slash_commands
from discord.ext import commands

from bot.models import DiscordGuild, Quake3Server
from bot.models.discord_user import DiscordUser
from bot.models.user_server_configuration import UserQuake3ServerConfiguration
from bot.quake3_bot import Quake3Bot
from bot.utils.trigrams import make_search_bank, query_search_bank

EXTRA_VALID_ADDRESSES = {
    "localhost",
    "::1",
}


class Quake3ServerCommands(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

    @slash_commands.command(
        name="addserver", description="Add a Quake 3 server to the bot for this Discord server"
    )
    @commands.has_permissions(manage_guild=True)
    async def add_server(self, inter: discord.Interaction, address: str, password: str):
        await inter.response.defer(ephemeral=True)

        address_without_port = address.split(":")[0]

        port = 27960
        if ":" in address:
            try:
                port = int(port)
            except ValueError:
                await inter.edit_original_response(content="Specified address is invalid.")
                return

        if not (
            validators.domain(address)
            or validators.ipv4(address_without_port)
            or validators.ipv6(address_without_port)
            or address_without_port.lower() in EXTRA_VALID_ADDRESSES
        ):
            await inter.edit_original_response(content="Specified address is invalid.")
            return

        try:
            await aioq3rcon.Client(host=address_without_port, port=port, password=password).connect(
                verify=True
            )
        except (ConnectionError, socket.gaierror):
            await inter.edit_original_response(content="Server could not be connected to.")
            return
        except aioq3rcon.IncorrectPasswordError:
            await inter.edit_original_response(content="Specified password is incorrect.")
            return

        db_guild, _ = await DiscordGuild.get_or_create(id=inter.guild_id)
        db_q3server = await Quake3Server.create(address=address, discord_guild=db_guild)
        await UserQuake3ServerConfiguration.create(
            server=db_q3server,
            discord_user=(await DiscordUser.get_or_create(id=inter.user.id))[0],
            password=password,
        )

        await inter.edit_original_response(content="Successfully added server!")

    async def rcon_autocomplete_server(
        self, inter: discord.Interaction, current: str
    ) -> list[slash_commands.Choice[Quake3Server]]:
        servers = await Quake3Server.filter(discord_guild__id=inter.guild_id)

        inter.extras["servers"] = {s.id: s for s in servers}

        if not current:  # show em all
            return [slash_commands.Choice(name=q3s.address, value=q3s.id) for q3s in servers][:10]

        search_bank_items = {s.address.lower() for s in servers}
        search_bank = make_search_bank(search_bank_items)
        results = {r.item for r in query_search_bank(search_bank, current) if r.similarity > 0.15}

        return [
            slash_commands.Choice(name=q3s.address, value=q3s.id)
            for q3s in servers
            if q3s.address.lower() in results
        ]

    @slash_commands.command(name="rcon", description="Send commands to your Quake III Server")
    @slash_commands.autocomplete(server=rcon_autocomplete_server)
    async def rcon(self, inter: discord.Interaction, server: int):
        await inter.response.defer()

        server: Quake3Server = inter.extras["servers"][server]

        await inter.edit_original_response(content=server.address)


async def setup(bot: Quake3Bot):
    await bot.add_cog(Quake3ServerCommands(bot))
