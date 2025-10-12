import asyncio
from aiogram import Bot, Dispatcher
from app.database import init_db
from app.handlers import start
from app.config import BOT_TOKEN


async def main():
    # Bazani tayyorlash
    await init_db()

    # Bot va dispatcher yaratamiz
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Routerlarni ulaymiz
    dp.include_router(start.router)

    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
