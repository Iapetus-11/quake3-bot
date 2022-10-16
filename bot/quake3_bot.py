import aiohttp
import arrow
import discord
from discord.ext import commands
from bot.utils.setup import setup_logging

from bot.config import CONFIG


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
        ]

    async def start(self, **kwargs) -> None:
        # load all the cogs
        for cog in self.cog_list:
            await self.load_extension(f"bot.cogs.{cog}")

        await super().start(CONFIG.DISCORD_BOT_TOKEN, **kwargs)

    async def on_ready(self) -> None:
        self.logger.info("Syncing slash commands...")
        await self.tree.sync()
        self.logger.info("Synced slash commands!")

    def default_embed(self) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.dark_red())

        embed.timestamp = arrow.utcnow().datetime

        embed.set_footer(text="Quake3 Bot", icon_url=self.user.avatar.url)

        return embed
