from aiogram.fsm.state import State, StatesGroup
import pytz
import io
from aiogram.types import BufferedInputFile
import matplotlib.pyplot as plt
from datetime import datetime
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.addition.inline import get_pagination_keyboard, get_expenses_action_keyboard
from app.database import Expense
from sqlalchemy import select, extract

ITEMS_PER_PAGE = 10


def get_pagination_keyboard(page: int, has_next: bool, year=None, month=None):
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="⬅️ Orqaga", callback_data=f"expenses_page:{page - 1}:{year}:{month}")
    if has_next:
        builder.button(text="➡️ Keyingisi", callback_data=f"expenses_page:{page + 1}:{year}:{month}")
    builder.adjust(2)
    return builder.as_markup()


async def show_expenses_page(target, session, user_id: int, page: int = 1, year=None, month=None, edit=False):
    PAGE_SIZE = 10
    offset = (page - 1) * PAGE_SIZE

    now = datetime.now(TZ)
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1

    query = select(Expense).where(Expense.user_id == user_id)

    if not year and not month:
        query = query.where(
            ((extract('year', Expense.created_at) == now.year) & (extract('month', Expense.created_at) == now.month))
            | ((extract('year', Expense.created_at) == last_month_year) & (extract('month', Expense.created_at) == last_month))
        )
    else:
        if year:
            query = query.where(extract('year', Expense.created_at) == year)
        if month:
            query = query.where(extract('month', Expense.created_at) == month)

    query = query.order_by(Expense.created_at.desc()).limit(PAGE_SIZE).offset(offset)
    result = await session.execute(query)
    expenses = result.scalars().all()
    has_next = len(expenses) == PAGE_SIZE

    if not expenses:
        await target.answer("Hech qanday harajat topilmadi.")
        return

    text = "📋 <b>Harajatlar ro'yxati</b>\n\n"
    for exp in expenses:
        text += (
            f"🆔 ID: {exp.id}\n"
            f"💰 Miqdor: {exp.amount:,} so‘m\n"
            f"📅 Sana: {exp.created_at.astimezone(TZ).strftime('%Y-%m-%d %H:%M')}\n"
            f"📝 Izoh: {exp.reason or '—'}\n"
            f"───────────────────────\n"
        )

    inline_kb = get_pagination_keyboard(page, has_next, year, month)

    if edit:
        await target.edit_text(text, reply_markup=inline_kb, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=inline_kb, parse_mode="HTML")
        await target.answer("👇 Quyidagi harakatlardan birini tanlang:", reply_markup=get_expenses_action_keyboard())


class DeleteExpense(StatesGroup):
    waiting_for_id = State()

class AddExpense(StatesGroup):
    amount = State()
    reason = State()
    date = State()



class CustomStats(StatesGroup):
    start_date = State()

TZ = pytz.timezone("Asia/Tashkent")


from aiogram import types
from sqlalchemy import select, extract, func
from datetime import datetime
import pytz
import io
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile
from app.database import Expense

TZ = pytz.timezone("Asia/Tashkent")


async def show_expense_statistics(message, session, user_id: int):
    now = datetime.now(TZ)
    year, month = now.year, now.month

    # 🔹 Hozirgi oy bo‘yicha harajatlar olish
    query = select(Expense.amount, Expense.created_at).where(
        (Expense.user_id == user_id)
        & (extract("year", Expense.created_at) == year)
        & (extract("month", Expense.created_at) == month)
    )
    result = await session.execute(query)
    expenses = result.all()

    if not expenses:
        await message.answer("📊 Hozircha bu oyda harajatlar yo‘q.")
        return

    # 🔹 Kunlik yig‘indi hisoblash
    daily_expenses = {}
    for amount, date in expenses:
        local_date = date.astimezone(TZ).date()
        daily_expenses[local_date.day] = daily_expenses.get(local_date.day, 0) + amount

    # 🔹 Oydagi kunlar soniga qarab massiv yasash
    import calendar
    _, days_in_month = calendar.monthrange(year, month)

    x_days = list(range(1, days_in_month + 1))
    y_amounts = [daily_expenses.get(day, 0) for day in x_days]

    # 🔹 Grafik yasash
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.figure(figsize=(8, 4))
    plt.plot(x_days, y_amounts, marker='o', linewidth=2, color='royalblue')
    plt.title(f"{now.strftime('%B %Y')} oyi harajatlari", fontsize=12)
    plt.xlabel("Kun", fontsize=10)
    plt.ylabel("Harajat (so‘m)", fontsize=10)
    plt.tight_layout()

    # 🔹 Grafikni yuborish
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    image = BufferedInputFile(buf.getvalue(), filename="monthly_stats.png")
    await message.answer_photo(photo=image, caption="📊 Joriy oy bo‘yicha harajatlar grafigi.")
