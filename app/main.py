import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.database import init_db
from app.handlers import (
    expense, start, statistics, tasks_add, tasks_list, tasks_assignment, tasks_see, create_project
)
from app.config import BOT_TOKEN
from app.addition.commands import set_bot_commands
from app.services.scheduler import setup_scheduler



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    try:
        await init_db()
        logger.info("📦 Ma'lumotlar bazasi muvaffaqiyatli yaratildi yoki allaqachon mavjud.")

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

        logger.info("🤖 Bot ishga tushdi va polling boshlandi.")
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"❌ Bot ishga tushirishda xatolik: {e}")

    finally:
        logger.info("🛑 Bot to‘xtatildi.")


if __name__ == "__main__":
    asyncio.run(main())
