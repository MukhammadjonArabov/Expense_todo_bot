from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from sqlalchemy import select, func
from app.database import async_session, Expense


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


# 🗓 YILLAR klaviaturasi
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


# 📅 OYLAR klaviaturasi
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
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_years_statistic")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
