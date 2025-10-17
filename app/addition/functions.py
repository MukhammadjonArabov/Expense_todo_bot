import io
import matplotlib.pyplot as plt
from app.database import async_session
from aiogram.fsm.state import State, StatesGroup
import pytz
import io
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    KeyboardButton, InputFile
import matplotlib.pyplot as plt
from datetime import datetime
from app.addition.inline import get_pagination_keyboard, get_expenses_action_keyboard
from app.database import Expense
from sqlalchemy import select, extract, func
import calendar
from app.database import User

ITEMS_PER_PAGE = 10

async def get_user(session, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()


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


async def get_years_keyboard_statistic(session, user_id: int):
    result = await session.execute(
        select(func.extract('year', Expense.created_at))
        .where(Expense.user_id == user_id)
        .distinct()
        .order_by(func.extract('year', Expense.created_at).desc())
    )
    years = [int(row[0]) for row in result.all()]

    keyboard = [
        [InlineKeyboardButton(text=f"📅 {year}", callback_data=f"stat_year:{user_id}:{year}")]
        for year in years
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def get_years_keyboard_for_months(session, user_id: int):
    result = await session.execute(
        select(func.extract('year', Expense.created_at))
        .where(Expense.user_id == user_id)
        .distinct()
        .order_by(func.extract('year', Expense.created_at).desc())
    )
    years = [int(row[0]) for row in result.all()]

    keyboard = [
        [InlineKeyboardButton(text=f"📆 {year}", callback_data=f"choose_year:{user_id}:{year}")]
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
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_years_statistic")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def show_months_for_statistic(target, user_id: int, year: int, edit=False):
    async with async_session() as session:
        result = await session.execute(
            select(func.extract('month', Expense.created_at))
            .where(
                (Expense.user_id == user_id)
                & (func.extract('year', Expense.created_at) == year)
            )
            .distinct()
            .order_by(func.extract('month', Expense.created_at).asc())
        )
        months = [int(row[0]) for row in result.all()]

    if not months:
        await target.answer("Bu yil uchun hech qanday harajat topilmadi.")
        return

    text = f"📊 {year}-yil uchun oy tanlang (statistika):"
    markup = get_months_keyboard_statistic(year, months)

    if edit:
        await target.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


async def generate_year_chart(year: int, data):
    months = [int(row[0]) for row in data]
    totals = [float(row[1]) for row in data]

    plt.figure(figsize=(7, 4))
    plt.bar(months, totals, color="skyblue")
    plt.title(f"{year}-yil bo‘yicha oylik harajatlar")
    plt.xlabel("Oy")
    plt.ylabel("So‘m")
    plt.xticks(months)
    plt.grid(True, linestyle="--", alpha=0.6)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return BufferedInputFile(buf.read(), filename=f"{year}_year_chart.png")


async def generate_month_chart(year: int, month: int, data):
    days = [int(row[0]) for row in data]
    totals = [float(row[1]) for row in data]

    plt.figure(figsize=(8, 4))
    plt.plot(days, totals, marker="o", linewidth=2, color="dodgerblue")
    plt.title(f"{year}-{month}-oy bo‘yicha kunlik harajatlar")
    plt.xlabel("Kun")
    plt.ylabel("So‘m")
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return BufferedInputFile(buf.read(), filename=f"{year}_{month}_month_chart.png")