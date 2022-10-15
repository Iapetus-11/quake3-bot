import aiohttp
import aiosqlite
import arrow
import discord
from discord.ext import commands
from bot.utils.setup import setup_logging

from bot.config import BotConfig


class MyBot(commands.AutoShardedBot):
    def __init__(self, config: BotConfig):
        super().__init__(
            case_insensitive=True,
            help_command=None,
            intents=discord.Intents.all(),
            command_prefix=config.COMMAND_PREFIX,
        )

        self.config = config

        self.logger = setup_logging()

        # these all have to be created later in an async context, see the start method
        self.db: aiosqlite.Connection = None
        self.aiohttp_client: aiohttp.ClientSession = None

        self.cog_list = [
            "core.events",
            "core.database",
            "commands.hello",
        ]

    async def start(self) -> None:
        async with aiohttp.ClientSession(
            raise_for_status=True
        ) as self.aiohttp_client, aiosqlite.connect(self.config.DATABASE_NAME) as self.db:
            # load all the cogs
            for cog in self.cog_list:
                await self.load_extension(f"bot.cogs.{cog}")

            await super().start(self.config.DISCORD_BOT_TOKEN)

    async def on_ready(self) -> None:
        self.logger.info("Syncing slash commands...")
        await self.tree.sync()
        self.logger.info("Synced slash commands!")

    def default_embed(self) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.purple())

        embed.timestamp = arrow.utcnow().datetime

        embed.set_footer(text="MyBot", icon_url=self.user.avatar.url)

        return embed
