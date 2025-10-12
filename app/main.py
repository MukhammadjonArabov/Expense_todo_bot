import asyncio
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN
from app.handlers import start
from app.database import init_db

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    await init_db()

    print("✅ Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
