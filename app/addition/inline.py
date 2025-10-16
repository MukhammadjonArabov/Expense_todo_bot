from aiogram import types, F
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_pagination_keyboard(page: int, has_next: bool):
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"expenses_page:{page - 1}")
        )
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️ Keyingilar", callback_data=f"expenses_page:{page + 1}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[nav_buttons]) if nav_buttons else None

def get_expenses_action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🗑 O'chirish"),
                KeyboardButton(text="🔙 Menyuga qaytish"),
            ],
            [
                KeyboardButton(text="📆 Yil va oy bo‘yicha ko‘rish"),
            ]
        ],
        resize_keyboard=True
    )


def get_expense_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Harajat qo'shish")],
            [types.KeyboardButton(text="📋 Harajatlar ro'yxati")],
            [types.KeyboardButton(text="📊 Harajatlar statistika")],
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_years_keyboard(years: list[int], user_id: int):
    keyboard = [
        [InlineKeyboardButton(text=f"📆 {year}", callback_data=f"choose_year:{user_id}:{year}")]
        for year in years
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_months_keyboard(year: int, months: list[int]):
    keyboard = []
    month_names = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
    ]

    for month in months:
        name = month_names[month - 1]
        keyboard.append([
            InlineKeyboardButton(
                text=f"📆 {name}",
                callback_data=f"choose_month:{year}:{month}"
            )
        ])

    # 🔙 Orqaga tugmasi
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_years")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_main_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Harajatlar"), types.KeyboardButton(text="📝 Vazifalar")]
        ],
        resize_keyboard=True
    )
    await message.answer("🏠 Asosiy menyu:", reply_markup=keyboard)


def get_pagination_keyboard(page: int, has_next: bool, year=None, month=None):
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️ Orqaga", callback_data=f"expenses_page:{page - 1}:{year}:{month}")
    if has_next:
        builder.button(text="➡️ Keyingisi", callback_data=f"expenses_page:{page + 1}:{year}:{month}")
    builder.adjust(2)
    return builder.as_markup()