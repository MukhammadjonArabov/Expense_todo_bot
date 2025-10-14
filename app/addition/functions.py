from aiogram.fsm.state import State, StatesGroup
import pytz
from app.addition.inline import get_pagination_keyboard, get_expenses_action_keyboard
from app.database import Expense
from sqlalchemy import select, func
from aiogram import types

ITEMS_PER_PAGE = 10

async def show_expenses_page(message_or_callback, session, user_id: int, page: int = 1):
    offset = (page - 1) * ITEMS_PER_PAGE

    total_expenses = await session.scalar(
        select(func.count(Expense.id)).where(Expense.user_id == user_id)
    )

    result = await session.execute(
        select(Expense)
        .where(Expense.user_id == user_id)
        .order_by(Expense.created_at.desc())
        .offset(offset)
        .limit(ITEMS_PER_PAGE)
    )
    expenses = result.scalars().all()

    if not expenses:
        await message_or_callback.answer("Hech qanday harajat yo‘q.")
        return

    text = f"📋 Harajatlar ro'yxati (sahifa {page}):\n\n"
    for exp in expenses:
        text += (
            f"🆔 ID: {exp.id}\n"
            f"📅 Sana: {exp.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"💰 Summa: {exp.amount} so'm\n"
            f"📝 Sabab: {exp.reason or 'Yo‘q'}\n\n"
        )

    has_next = total_expenses > offset + ITEMS_PER_PAGE
    pagination_keyboard = get_pagination_keyboard(page, has_next)
    reply_keyboard = get_expenses_action_keyboard()

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=pagination_keyboard)
        await message_or_callback.message.answer("👇 Quyidagi amallardan birini tanlang:", reply_markup=reply_keyboard)
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=pagination_keyboard)
        await message_or_callback.answer("👇 Quyidagi amallardan birini tanlang:", reply_markup=reply_keyboard)


class DeleteExpense(StatesGroup):
    waiting_for_id = State()

class AddExpense(StatesGroup):
    amount = State()
    reason = State()
    date = State()



class CustomStats(StatesGroup):
    start_date = State()

TZ = pytz.timezone("Asia/Tashkent")