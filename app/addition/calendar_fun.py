from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import calendar

# === 1. YIL TANLASH ===
def generate_years_keyboard(start_year=2024, end_year=None):
    """Yil tanlash uchun inline keyboard"""
    now = datetime.now()
    if end_year is None:
        end_year = now.year + 1  # faqat joriy va kelasi yil

    keyboard = []
    for year in range(start_year, end_year + 1):
        if year < now.year:
            continue
        keyboard.append([
            InlineKeyboardButton(text=str(year), callback_data=f"year:{year}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# === 2. OY TANLASH ===
def generate_months_keyboard(selected_year: int):
    """Oyni tanlash uchun keyboard"""
    months = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
    ]
    now = datetime.now()
    keyboard, row = [], []

    for i, month in enumerate(months, start=1):
        if selected_year == now.year and i < now.month:
            continue
        row.append(InlineKeyboardButton(text=month, callback_data=f"month:{selected_year}:{i}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_years")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# === 3. KUN TANLASH ===
def generate_days_keyboard(selected_year: int, selected_month: int):
    """Kunni tanlash uchun keyboard"""
    now = datetime.now()
    _, days_in_month = calendar.monthrange(selected_year, selected_month)
    keyboard, row = [], []

    for day in range(1, days_in_month + 1):
        current_date = datetime(selected_year, selected_month, day)
        if current_date.date() < now.date():
            continue
        row.append(InlineKeyboardButton(text=str(day), callback_data=f"day:{selected_year}:{selected_month}:{day}"))
        if len(row) == 7:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"back_to_months:{selected_year}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
