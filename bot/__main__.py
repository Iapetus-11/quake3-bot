import asyncio

from tortoise import Tortoise

from bot.config import CONFIG
from bot.quake3_bot import Quake3Bot


async def async_main():
    await Tortoise.init(
        db_url=CONFIG.DATABASE_URL,
        modules={
            "models": ["bot.models"],
        },
    )

    bot = Quake3Bot()

    async with bot:
        await bot.start()


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
