import aiohttp
import arrow
import discord
from discord.ext import commands

from bot.config import CONFIG
from bot.models import DiscordGuild, DiscordUser
from bot.utils.setup import setup_logging


class Quake3Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            case_insensitive=True,
            help_command=None,
            intents=discord.Intents.default(),
            command_prefix=commands.when_mentioned,
        )

        self.logger = setup_logging()

        # these all have to be created later in an async context, see the start method
        self.aiohttp_client: aiohttp.ClientSession | None = None

        self.cog_list = [
            "core.events",
            "commands.owner",
            "commands.help",
            "commands.quake3_server",
        ]

    async def get_error_channel(self) -> discord.TextChannel:
        await self.wait_until_ready()
        return self.get_channel(CONFIG.ERROR_CHANNEL_ID)

    async def start(self, **kwargs) -> None:
        # load all the cogs
        for cog in self.cog_list:
            await self.load_extension(f"bot.cogs.{cog}")
            self.logger.info(f"Loaded extension: {cog}")

        await super().start(CONFIG.DISCORD_BOT_TOKEN, **kwargs)

    async def on_ready(self) -> None:
        self.logger.info("Bot is connected and ready!")

        self.logger.info("Syncing slash commands...")
        self.tree.copy_global_to(guild=self.get_guild(CONFIG.DEVELOPMENT_GUILD_ID))
        await self.tree.sync()
        self.logger.info("Synced slash commands!")

    def default_embed(self) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.dark_red())

        embed.timestamp = arrow.utcnow().datetime

        embed.set_footer(text="Quake III Bot", icon_url=self.user.avatar.url)

        return embed

    @staticmethod
    async def get_inter_db_data(inter: discord.Interaction) -> tuple[DiscordGuild, DiscordUser]:
        return (await DiscordGuild.get_or_create(id=inter.guild_id))[0], (
            await DiscordUser.get_or_create(id=inter.user.id)
        )[0]
