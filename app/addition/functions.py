from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import pytz
from datetime import datetime
from app.database import Expense
from sqlalchemy import select, extract
from aiogram import types
from app.database import User
from app.keyboards.expanse_main import get_pagination_keyboard, get_expenses_action_keyboard, get_expense_keyboard

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

    inline_kb = await get_pagination_keyboard(page, has_next, year, month)

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


async def back_to_menu(message: types.Message):
    await message.answer(
        "📋 Siz asosiy menyuga qaytdingiz.",
        reply_markup=get_expense_keyboard()
    )


async def cancel_adding_expense(message: types.Message, state: FSMContext):
    """Harajat qo‘shish jarayonini bekor qilish"""
    await state.clear()
    await back_to_menu(message)
