from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

async def get_team_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📂 Mening loyhalarim"),
                KeyboardButton(text="👥 Qatnashganlarim")
            ],
            [
                KeyboardButton(text="🔙 Ortga")
            ],
        ],
        resize_keyboard=True,
    )

async def get_my_projects_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Yangi loyiha"),
                KeyboardButton(text="📝 Vazifa qo‘shish")
            ],
            [
                KeyboardButton(text="🛠 Loyihani o‘zgartirish"),
                KeyboardButton(text="✏️ Vazifalarni o‘zgartirish")
            ],
            [
                KeyboardButton(text="🔙 Ortga")
            ],
        ],
        resize_keyboard=True,
    )

async def get_joined_projects_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Loyhalar ro‘yxati")],
            [KeyboardButton(text="🔙 Ortga")],
        ],
        resize_keyboard=True,
    )

async def cancel_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )