from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Message
)
from sqlalchemy import select, func
from app.database import Expense



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
                KeyboardButton(text="📆 Yil va oy bo‘yicha ko‘rish"),
                KeyboardButton(text="🗑 O'chirish"),
            ],
            [
                KeyboardButton(text="🔙 Menyuga qaytish"),
            ]
        ],
        resize_keyboard=True
    )


def get_expense_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Harajat qo'shish")],
            [KeyboardButton(text="📋 Harajatlar ro'yxati")],
            [KeyboardButton(text="📊 Harajatlar statistika")],
            [KeyboardButton(text="⬅️ Orqaga")]
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


async def show_main_menu(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Harajatlar"), KeyboardButton(text="📝 Vazifalar")]
        ],
        resize_keyboard=True
    )
    await message.answer("🏠 Asosiy menyu:", reply_markup=keyboard)

async def phone_menu(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "👋 Salom! Iltimos, ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
        reply_markup=keyboard
    )



def get_pagination_keyboard(page: int, has_next: bool, year=None, month=None):
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️ Orqaga", callback_data=f"expenses_page:{page - 1}:{year}:{month}")
    if has_next:
        builder.button(text="➡️ Keyingisi", callback_data=f"expenses_page:{page + 1}:{year}:{month}")
    builder.adjust(2)
    return builder.as_markup()

def get_statistics_action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📆 Oylik statistika"),
                KeyboardButton(text="📅 Yillik statistika"),
            ],
            [KeyboardButton(text="🔙 Menyuga qaytish")],
        ],
        resize_keyboard=True
    )


async def get_years_keyboard_statistic(session, user_id: int):
    result = await session.execute(
        select(func.extract('year', Expense.created_at))
        .where(Expense.user_id == user_id)
        .distinct()
        .order_by(func.extract('year', Expense.created_at).desc())
    )
    years = [int(row[0]) for row in result.all()]

    keyboard = [
        [InlineKeyboardButton(
            text=f"📅 {year}-yil",
            callback_data=f"choose_year_statistic:{user_id}:{year}"
        )]
        for year in years
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_months_keyboard_statistic(year: int, months: list[int]):
    month_names = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
    ]

    keyboard = [
        [InlineKeyboardButton(
            text=f"📆 {month_names[m - 1]}",
            callback_data=f"choose_month_statistic:{year}:{m}"
        )]
        for m in months
    ]
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"back_to_years_month_statistic")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Menyuga qaytish")]
        ],
        resize_keyboard=True
    )

