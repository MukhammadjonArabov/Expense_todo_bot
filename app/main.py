import asyncio
from aiogram import Bot, Dispatcher
from app.database import init_db
from app.handlers import expense, start, statistics
from app.config import BOT_TOKEN
from app.addition.commands import set_bot_commands


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()


    dp.include_router(start.router)
    dp.include_router(expense.router)
    dp.include_router(statistics.router)

    await set_bot_commands(bot)

    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
