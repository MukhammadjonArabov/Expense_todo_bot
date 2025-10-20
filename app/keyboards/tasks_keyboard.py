from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_statistics_action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Shaxsiy"),
                KeyboardButton(text="👥 Jamoviy")
            ],
            [KeyboardButton(text="🔙 Menyuga qaytish")],
        ],
        resize_keyboard=True
    )