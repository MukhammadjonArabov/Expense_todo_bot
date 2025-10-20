from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_tasks_action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Shaxsiy"),
                KeyboardButton(text="👥 Jamoviy")
            ],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )

async def get_personal_tasks_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Vazifa qo‘shish")],
            [KeyboardButton(text="📋 Vazifalar ro‘yxati")],
            [KeyboardButton(text="✅ Bajarilgan vazifalar")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

async def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ To‘xtatish")]
        ],
        resize_keyboard=True
    )