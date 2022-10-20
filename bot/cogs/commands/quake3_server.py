import socket
import time

import aioq3rcon
import discord
import validators
from aioq3rcon import RCONError
from discord import app_commands as slash_commands
from discord.ext import commands

from bot.models import Quake3Server
from bot.models.user_server_configuration import UserQuake3ServerConfiguration
from bot.quake3_bot import Quake3Bot
from bot.utils.text import truncate_string, validate_q3_identifier
from bot.utils.trigrams import make_search_bank, query_search_bank

EXTRA_VALID_ADDRESSES = {
    "localhost",
    "::1",
}


class Quake3ServerPasswordSetModal(discord.ui.Modal, title="Set Quake III server password"):
    password = discord.ui.TextInput(label="Password", max_length=64)

    continuation_inter: discord.Interaction

    async def on_submit(self, inter: discord.Interaction, /) -> None:
        self.continuation_inter = inter


class Quake3ServerCommands(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

    @staticmethod
    async def send_rcon_commands(
        q3_server: Quake3Server,
        q3_server_config: UserQuake3ServerConfiguration,
        commands: list[str],
        *,
        interpret: bool = True,
    ) -> list[str]:
        try:
            responses = []

            async with aioq3rcon.Client(
                host=q3_server.host, port=q3_server.port, password=q3_server_config.password
            ) as client:
                for command in commands:
                    responses.append(await client.send_command(command, interpret=interpret))

            return responses
        except (ConnectionError, socket.gaierror):
            raise RCONError("Server could not be connected to.")
        except aioq3rcon.IncorrectPasswordError:
            await q3_server_config.delete()
            raise RCONError("Specified password is incorrect.")

    async def get_inter_user_q3_server_config(
        self, inter: discord.Interaction, q3_server: Quake3Server, *, ephemeral: bool = False
    ) -> tuple[discord.Interaction, UserQuake3ServerConfiguration]:
        _, db_user = await self.bot.get_inter_db_data(inter)
        q3_server_config: UserQuake3ServerConfiguration = await q3_server.configurations.filter(
            discord_user=db_user
        ).first()

        if q3_server_config is None:
            await inter.response.send_modal(
                password_modal := Quake3ServerPasswordSetModal(timeout=60)
            )
            await password_modal.wait()
            q3_server_config = await UserQuake3ServerConfiguration.create(
                server=q3_server, discord_user=db_user, password=password_modal.password.value
            )
            inter = password_modal.continuation_inter

        await inter.response.defer(ephemeral=ephemeral)

        return inter, q3_server_config

    @slash_commands.command(
        name="addserver", description="Add a Quake III server to the bot for this Discord server"
    )
    @commands.has_permissions(manage_guild=True)
    async def add_server(self, inter: discord.Interaction, address: str, password: str):
        await inter.response.defer(ephemeral=True)

        if await Quake3Server.filter(address=address, discord_guild__id=inter.guild_id).first():
            await inter.edit_original_response(content="You cannot add a duplicate server.")
            return

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
            async with aioq3rcon.Client(host=address_without_port, port=port, password=password):
                pass
        except (ConnectionError, socket.gaierror):
            await inter.edit_original_response(content="Server could not be connected to.")
            return
        except aioq3rcon.IncorrectPasswordError:
            await inter.edit_original_response(content="Specified password is incorrect.")
            return

        db_guild, db_user = await self.bot.get_inter_db_data(inter)
        db_q3server = await Quake3Server.create(address=address, discord_guild=db_guild)
        await UserQuake3ServerConfiguration.create(
            server=db_q3server,
            discord_user=db_user,
            password=password,
        )

        await inter.edit_original_response(content="Successfully added server!")

    # noinspection PyMethodMayBeStatic
    async def autocomplete_server(
        self, inter: discord.Interaction, current: str
    ) -> list[slash_commands.Choice[Quake3Server]]:
        servers = await Quake3Server.filter(discord_guild__id=inter.guild_id)

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
    @slash_commands.autocomplete(server=autocomplete_server)  # type: ignore
    async def rcon(self, inter: discord.Interaction, server: int, *, command: str):
        server = await Quake3Server.get(id=server)
        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        try:
            responses = await self.send_rcon_commands(
                server, q3_server_config, [command], interpret=True
            )
        except RCONError as e:
            await inter.edit_original_response(content=e.args[0])
            return

        response = truncate_string("\n".join(responses).replace("`", ""), 2000 - 120)

        await inter.edit_original_response(
            content=f"```\uFEFF{truncate_string(command.replace('`', ''), 20)}``````\n\uFEFF{response}```",
        )

    @slash_commands.command(
        name="setmaprotation",
        description="Set the map rotation of the specified server, please enter map codes separated by spaces",
    )
    @slash_commands.autocomplete(server=autocomplete_server)  # type: ignore
    async def set_map_rotation(self, inter: discord.Interaction, server: int, *, maps: str):
        server = await Quake3Server.get(id=server)
        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        maps = [
            m for m in maps.replace(",", " ").replace("  ", " ").replace("  ", " ").split() if m
        ]

        if len(maps) > 256:
            await inter.edit_original_response(content="Map string too long.")
            return

        if len(maps) < 1:
            await inter.edit_original_response(content="No valid maps specified.")
            return

        for q3_map in maps:
            if not validate_q3_identifier(q3_map):
                await inter.edit_original_response(
                    content=f"Invalid map specified: `{discord.utils.escape_markdown(q3_map)}`"
                )
                return

        mv_prefix = "m"

        q3_commands = list[str]()

        for i, q3_map in enumerate(maps, start=1):
            q3_commands.append(
                f'set {mv_prefix}{i} "map {q3_map} ; set nextmap vstr {mv_prefix}{1 if i == len(maps) else i + 1}"'
            )

        q3_commands.append(f"vstr {mv_prefix}1")

        try:
            await self.send_rcon_commands(server, q3_server_config, q3_commands, interpret=True)
        except RCONError as e:
            await inter.edit_original_response(content=e.args[0])
            return

        q3_commands = "\n".join(q3_commands)

        await inter.edit_original_response(
            content=f"Successfully updated map rotation!\n\nCommand Ran:\n```\n{q3_commands}\n```"
        )

    @slash_commands.command(
        name="setmap", description="Set the current map on the specified server"
    )
    @slash_commands.autocomplete(server=autocomplete_server)
    async def set_map(self, inter: discord.Interaction, server: int, map: str):
        server = await Quake3Server.get(id=server)
        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        if not validate_q3_identifier(map) or len(map) > 64:
            await inter.edit_original_response(content="Invalid map specified.")
            return

        try:
            responses = await self.send_rcon_commands(server, q3_server_config, [f"map {map}"])
        except RCONError as e:
            await inter.edit_original_response(content=e.args[0])
            return

        if responses[0].startswith("Can't find map"):
            await inter.edit_original_response(content="Server could not find specified map.")
            return

        await inter.edit_original_response(content="Successfully set current map!")

    @slash_commands.command(
        name="serverping", description="Get the latency between the specified server and the bot"
    )
    @slash_commands.autocomplete(server=autocomplete_server)  # type: ignore
    async def server_ping(self, inter: discord.Interaction, server: int):
        server = await Quake3Server.get(id=server)
        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        try:
            async with aioq3rcon.Client(
                host=server.host, port=server.port, password=q3_server_config.password
            ) as client:
                start = time.perf_counter_ns()
                await client.send_command("heartbeat", interpret=False)
                elapsed_ms = (time.perf_counter_ns() - start) * 1e-6

        except (ConnectionError, socket.gaierror):
            await inter.edit_original_response(content="Server could not be connected to.")
            return
        except aioq3rcon.IncorrectPasswordError:
            await q3_server_config.delete()
            await inter.edit_original_response(content="Specified password is incorrect.")
            return

        await inter.edit_original_response(content=f"Server responded in `{elapsed_ms:0.2f} ms`")


async def setup(bot: Quake3Bot):
    await bot.add_cog(Quake3ServerCommands(bot))
