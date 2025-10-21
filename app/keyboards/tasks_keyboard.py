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
            [
                KeyboardButton(text="➕ Vazifa qo‘shish"),
                KeyboardButton(text="📋 Vazifalar ro‘yxati")
            ],
            [
                KeyboardButton(text="✍️ Bajarilganlarni belgilash"),
                KeyboardButton(text="⬅️ Ortga qaytish")
            ],

        ],
        resize_keyboard=True
    )

async def get_tasks_list_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅ Bajarilganlar"),
                KeyboardButton(text="❌ Bajarilmaganlar")
            ],
            [
                KeyboardButton(text="🕒 Bajarilishi keraklar"),
                KeyboardButton(text="⬅️ Ortga")
            ]
        ],
        resize_keyboard=True
    )

async def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Qaytish")]
        ],
        resize_keyboard=True
    )