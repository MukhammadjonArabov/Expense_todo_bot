from aiogram.types import BotCommand
from aiogram import Bot


async def set_bot_commands(bot: Bot):
    """
    Bot komandalarini Telegramda avtomatik ro'yxatdan o'tkazadi.
    Foydalanuvchi botni ochganda /start, /help, /menu komandalarini ko'radi.
    """
    commands = [
        BotCommand(command="start", description="Botni ishga tushurish"),
        BotCommand(command="help", description="Yordam olish"),
        BotCommand(command="menu", description="Asosiy menyuga qaytish"),
    ]
    await bot.set_my_commands(commands)