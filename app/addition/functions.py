from aiogram.fsm.context import FSMContext
import pytz
from datetime import datetime
from app.database import Expense, PersonalTask
from sqlalchemy import select, extract, func
from aiogram import types
from app.database import User
from app.database import async_session
from app.keyboards.expanse_main import get_pagination_keyboard, get_expenses_action_keyboard, get_expense_keyboard

ITEMS_PER_PAGE = 10
TZ = pytz.timezone("Asia/Tashkent")

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


async def cancel_adding_expense(message: types.Message, state: FSMContext):
    """Harajat qo‘shish jarayonini bekor qilish"""
    await state.clear()
    await message.answer(
        "📋 Siz asosiy menyuga qaytdingiz.",
        reply_markup=get_expense_keyboard()
    )

async def get_task_statistics(telegram_id: int):
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            return {
                "total": 0,
                "completed": 0,
                "not_completed": 0,
                "upcoming": 0
            }

        now = datetime.now(TZ).date()
        total_query = select(func.count()).where(PersonalTask.user_id == user.id)
        total = (await session.execute(total_query)).scalar() or 0

        completed_query = select(func.count()).where(
            PersonalTask.user_id == user.id,
            PersonalTask.is_completed == 1
        )
        completed = (await session.execute(completed_query)).scalar() or 0

        not_completed_query = select(func.count()).where(
            PersonalTask.user_id == user.id,
            PersonalTask.is_completed == 0,
            PersonalTask.deadline <= now
        )
        not_completed = (await session.execute(not_completed_query)).scalar() or 0

        upcoming_query = select(func.count()).where(
            PersonalTask.user_id == user.id,
            PersonalTask.is_completed == 0,
            PersonalTask.deadline > now
        )
        upcoming = (await session.execute(upcoming_query)).scalar() or 0

        return {
            "total": total,
            "completed": completed,
            "not_completed": not_completed,
            "upcoming": upcoming
        }

