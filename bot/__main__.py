import asyncio
from bot.my_bot import MyBot
from bot.config import load_config


async def main():
    config = load_config()

    bot = MyBot(config)

    async with bot:
        await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
