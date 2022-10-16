import asyncio

from tortoise import Tortoise

from bot.quake3_bot import Quake3Bot
from bot.config import CONFIG


async def async_main():
    await Tortoise.init(
        db_url=f'sqlite://{CONFIG.DATABASE_URI}',
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
