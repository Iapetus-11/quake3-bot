import socket
import time

import aioq3rcon
import discord
import validators
from aioq3rcon import RCONError
from discord import app_commands as slash_commands
from discord.ext import commands

from bot.data.quake3 import DEFAULT_Q3_MAP_FILES
from bot.models import Quake3Server
from bot.models.user_server_configuration import UserQuake3ServerConfiguration
from bot.quake3_bot import Quake3Bot
from bot.utils.interactions import edit_original_or_followup
from bot.utils.text import text_to_discord_file, validate_q3_identifier
from bot.utils.trigrams import make_search_bank, query_search_bank

EXTRA_VALID_ADDRESSES = {
    "localhost",
    "::1",
}


MSG_CONNECTION_ERROR = "Server could not be connected to."
MSG_INCORRECT_PASSWORD = "Server password is incorrect."


class Quake3ServerPasswordSetModal(discord.ui.Modal, title="Set Quake III server password"):
    password = discord.ui.TextInput(label="Password", max_length=64)

    continuation_inter: discord.Interaction

    async def on_submit(self, inter: discord.Interaction, /) -> None:
        self.continuation_inter = inter


class Quake3ServerCommands(commands.Cog):
    def __init__(self, bot: Quake3Bot):
        self.bot = bot

        self.q3_maps_search_bank = make_search_bank(
            [f.removesuffix(".bsp") for f in DEFAULT_Q3_MAP_FILES if f.endswith(".bsp")]
        )

    @staticmethod
    async def send_rcon_commands(
        q3_server: Quake3Server,
        q3_server_config: UserQuake3ServerConfiguration,
        rcon_commands: list[str],
        *,
        interpret: bool = True,
    ) -> list[str]:
        try:
            responses = []

            async with aioq3rcon.Client(
                host=q3_server.host, port=q3_server.port, password=q3_server_config.password
            ) as client:
                for command in rcon_commands:
                    responses.append(await client.send_command(command, interpret=interpret))

            return responses
        except (ConnectionError, socket.gaierror):
            raise RCONError(MSG_CONNECTION_ERROR)
        except aioq3rcon.IncorrectPasswordError:
            await q3_server_config.delete()
            raise RCONError(MSG_INCORRECT_PASSWORD)

    # noinspection PyMethodMayBeStatic
    async def autocomplete_server_id(
        self, inter: discord.Interaction, current: str
    ) -> list[slash_commands.Choice[Quake3Server]]:
        servers = await Quake3Server.filter(discord_guild__id=inter.guild_id)

        if not servers:
            return []

        if not current:  # show em all
            return [slash_commands.Choice(name=q3s.address, value=q3s.id) for q3s in servers][:25]

        search_bank_items = {s.address.lower() for s in servers}
        search_bank = make_search_bank(search_bank_items)
        results = [r.item for r in query_search_bank(search_bank, current) if r.similarity > 0.15]

        return [
            slash_commands.Choice(name=q3s.address, value=q3s.id)
            for q3s in servers
            if q3s.address.lower() in results
        ]

    async def autocomplete_map(
        self, inter: discord.Interaction, current: str
    ) -> list[slash_commands.Choice[str]]:
        return [
            slash_commands.Choice(name=m, value=m)
            for m in dict.fromkeys(
                [current, *[r.item for r in query_search_bank(self.q3_maps_search_bank, current)]][
                    :25
                ]
            ).keys()
        ]

    @staticmethod
    async def attempt_get_server(
        inter: discord.Interaction, server_id: int, *, edit_original: bool = False
    ) -> Quake3Server | None:
        server = await Quake3Server.get_or_none(id=server_id)

        if server is None:
            if edit_original:
                await inter.edit_original_response(content="That server does not exist.")
            else:
                await inter.response.send_message(
                    content="That server does not exist.", ephemeral=True
                )

        return server

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
        name="servers", description="List out the Quake III servers added to this Discord server"
    )
    async def servers(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=True)

        servers = await Quake3Server.filter(discord_guild__id=inter.guild_id).values_list(
            "address", flat=True
        )

        if servers:
            await inter.edit_original_response(content=f"Servers: `{'`, `'.join(servers)}`")
        else:
            await inter.edit_original_response(
                content="This Discord server has no linked Quake III servers. "
                "You can use `/addserver` to add a new Quake III server."
            )

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
            await inter.edit_original_response(content=MSG_CONNECTION_ERROR)
            return
        except aioq3rcon.IncorrectPasswordError:
            await inter.edit_original_response(content=MSG_INCORRECT_PASSWORD)
            return

        db_guild, db_user = await self.bot.get_inter_db_data(inter)
        db_q3server = await Quake3Server.create(address=address, discord_guild=db_guild)
        await UserQuake3ServerConfiguration.create(
            server=db_q3server,
            discord_user=db_user,
            password=password,
        )

        await inter.edit_original_response(content="Successfully added server!")

    @slash_commands.command(
        name="removeserver", description="Remove a Quake III server from this Discord server"
    )
    @slash_commands.rename(server_id="server")
    @slash_commands.autocomplete(server_id=autocomplete_server_id)  # type: ignore
    @commands.has_permissions(manage_guild=True)
    async def remove_server(self, inter: discord.Interaction, server_id: int):
        await inter.response.defer(ephemeral=True)

        if server := await self.attempt_get_server(inter, server_id):
            await server.delete()
            await inter.edit_original_response(
                content=f"Removed server `{server.address}` from this Discord server."
            )

    @slash_commands.command(name="rcon", description="Send commands to your Quake III Server")
    @slash_commands.rename(server_id="server")
    @slash_commands.autocomplete(server_id=autocomplete_server_id)  # type: ignore
    async def rcon(self, inter: discord.Interaction, server_id: int, *, command: str):
        if not (server := await self.attempt_get_server(inter, server_id)):
            return

        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        try:
            responses = await self.send_rcon_commands(
                server, q3_server_config, [command], interpret=True
            )
        except RCONError as e:
            await edit_original_or_followup(inter, content=e.args[0])
            return

        await edit_original_or_followup(
            inter,
            attachments=[text_to_discord_file("\n".join(responses), file_name="rcon_response.txt")],
        )

    @slash_commands.command(
        name="setmap", description="Set the current map on the specified server"
    )
    @slash_commands.rename(server_id="server", q3_map="map")
    @slash_commands.autocomplete(server_id=autocomplete_server_id, q3_map=autocomplete_map)  # type: ignore
    async def set_map(self, inter: discord.Interaction, server_id: int, q3_map: str):
        if not (server := await self.attempt_get_server(inter, server_id)):
            return

        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, server, ephemeral=True
        )

        if not validate_q3_identifier(q3_map) or len(q3_map) > 64:
            await edit_original_or_followup(inter, content="Invalid map specified.")
            return

        try:
            responses = await self.send_rcon_commands(server, q3_server_config, [f"map {q3_map}"])
        except RCONError as e:
            await edit_original_or_followup(inter, content=e.args[0])
            return

        if responses[0].startswith("Can't find map"):
            await edit_original_or_followup(inter, content="Server could not find specified map.")
            return

        await edit_original_or_followup(inter, content="Successfully set current map!")

    @slash_commands.command(
        name="setmaprotation",
        description="Set the map rotation of the specified server, please enter map codes separated by spaces",
    )
    @slash_commands.rename(server_id="server", q3_maps_str="maps")
    @slash_commands.autocomplete(server_id=autocomplete_server_id)  # type: ignore
    async def set_map_rotation(
        self, inter: discord.Interaction, server_id: int, *, q3_maps_str: str
    ):
        if not (q3_server := await self.attempt_get_server(inter, server_id)):
            return

        inter, q3_server_config = await self.get_inter_user_q3_server_config(
            inter, q3_server, ephemeral=True
        )

        maps = [
            m
            for m in q3_maps_str.replace(",", " ").replace("  ", " ").replace("  ", " ").split()
            if m
        ]

        if len(maps) > 256:
            await edit_original_or_followup(inter, content="Map string too long.")
            return

        if len(maps) < 1:
            await edit_original_or_followup(inter, content="No valid maps specified.")
            return

        for q3_map in maps:
            if not validate_q3_identifier(q3_map):
                await edit_original_or_followup(
                    inter,
                    content=f"Invalid map specified: `{discord.utils.escape_markdown(q3_map)}`",
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
            await self.send_rcon_commands(q3_server, q3_server_config, q3_commands, interpret=True)
        except RCONError as e:
            await edit_original_or_followup(inter, content=e.args[0])
            return

        await edit_original_or_followup(
            inter,
            content="Successfully updated map rotation!",
            attachments=[
                text_to_discord_file("\n".join(q3_commands), file_name="map_rotation_commands.txt")
            ],
        )

    @slash_commands.command(
        name="serverping", description="Get the latency between the specified server and the bot"
    )
    @slash_commands.rename(server_id="server")
    @slash_commands.autocomplete(server_id=autocomplete_server_id)  # type: ignore
    async def server_ping(self, inter: discord.Interaction, server_id: int):
        if not (server := await self.attempt_get_server(inter, server_id)):
            return

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
            await edit_original_or_followup(inter, content=MSG_CONNECTION_ERROR)
            return
        except aioq3rcon.IncorrectPasswordError:
            await q3_server_config.delete()
            await edit_original_or_followup(inter, content=MSG_INCORRECT_PASSWORD)
            return

        await edit_original_or_followup(
            inter, content=f"Server responded in `{elapsed_ms:0.2f} ms`"
        )


async def setup(bot: Quake3Bot):
    await bot.add_cog(Quake3ServerCommands(bot))
