import asyncio
from aiogram import Bot, Dispatcher
from app.database import init_db
from app.handlers import (
    expense, start, statistics, tasks_add, tasks_list, tasks_assignment, tasks_see, create_project
)
from app.config import BOT_TOKEN
from app.addition.commands import set_bot_commands
from app.services.scheduler import setup_scheduler


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()


    dp.include_router(start.router)
    dp.include_router(expense.router)
    dp.include_router(statistics.router)
    dp.include_router(tasks_add.router)
    dp.include_router(tasks_list.router)
    dp.include_router(tasks_assignment.router)
    dp.include_router(tasks_see.router)
    dp.include_router(create_project.router)

    await setup_scheduler(bot)
    await set_bot_commands(bot)

    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
