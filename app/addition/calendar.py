from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import calendar
from app.addition.functions import TZ

def generate_month_days_keyboard(year: int, month: int):
    markup = InlineKeyboardMarkup(row_width=7)

    now = datetime.now(TZ).date()
    month_days = calendar.monthrange(year, month)[1]
    week_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    # Haftaning kunlari (sarlavha)
    markup.row(*[InlineKeyboardButton(text=d, callback_data="ignore") for d in week_days])

    # Oy boshi kuni (haftaning qaysi kunidan boshlanishi)
    first_weekday = datetime(year, month, 1).weekday()  # 0 = Dushanba
    empty_buttons = [InlineKeyboardButton(" ", callback_data="ignore")] * first_weekday
    if empty_buttons:
        markup.row(*empty_buttons)

    buttons = []
    for day in range(1, month_days + 1):
        current_date = datetime(year, month, day, tzinfo=TZ).date()

        # O‘tgan kunlar bosilmaydi
        if current_date < now:
            btn = InlineKeyboardButton(text=f"❌{day}", callback_data="ignore")
        else:
            btn = InlineKeyboardButton(text=str(day), callback_data=f"pick_date:{year}-{month}-{day}")

        buttons.append(btn)

        # Haftani to‘ldirib chiqish
        if len(buttons) == 7:
            markup.row(*buttons)
            buttons = []

    if buttons:
        markup.row(*buttons)

    # Oy o‘zgarish tugmalari
    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year = year if month > 1 else year - 1
    next_year = year if month < 12 else year + 1

    markup.row(
        InlineKeyboardButton("⬅️ Oldingi", callback_data=f"change_month:{prev_year}-{prev_month}"),
        InlineKeyboardButton("➡️ Keyingi", callback_data=f"change_month:{next_year}-{next_month}")
    )

    return markup
