from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.database import async_session, Expense, User
from sqlalchemy import select, delete, func
from datetime import datetime, timedelta
import pytz

router = Router()

# FSM states
class AddExpense(StatesGroup):
    amount = State()
    reason = State()
    date = State()


class DeleteExpense(StatesGroup):
    id = State()

class CustomStats(StatesGroup):
    start_date = State()

TZ = pytz.timezone("Asia/Tashkent")

def get_expense_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Harajat qo'shish")],
            [types.KeyboardButton(text="📋 Harajatlar ro'yxati")],
            [types.KeyboardButton(text="❌ Harajatni o'chirish")],
            [types.KeyboardButton(text="📊 Harajatlar statistika")],
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

async def get_user(session, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()

@router.message(F.text.contains("Harajatlar"))
async def expense_menu(message: types.Message):
    await message.answer(
        "💰 Harajatlar bo'limiga o'tdingiz. Quyidagilardan birini tanlang:",
                         reply_markup=get_expense_keyboard()
                         )

@router.message(F.text == "➕ Harajat qo'shish")
async def add_expense_start(message: types.Message, state: FSMContext):
    await message.answer("Harajat summasini kiriting (musbat butun son):")
    await state.set_state(AddExpense.amount)

@router.message(AddExpense.amount)
async def add_expense_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
        await state.update_data(amount=amount)
        await message.answer("Harajat sababini kiriting"
                             "Agar besabab bo'lsa - belgini kiriting!")
        await state.set_state(AddExpense.reason)
    except ValueError:
        await message.answer("Iltimos, to'g'ri musbat butun son kiriting!")

@router.message(AddExpense.reason)
async def add_expense_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip() if message.text.strip() != "-" else None
    await state.update_data(reason=reason)
    await message.answer("Sana va vaqtni kiriting 2025-10-14 14:30 yoki"
                         "hozirgi vaqtni belgilash uchun - belgini kiritng!")
    await state.set_state(AddExpense.date)

@router.message(AddExpense.date)
async def add_expense_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id

    if message.text.strip() == "-":
        created_at = datetime.now(TZ)
    else:
        try:
            created_at = TZ.localize(datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M"))
        except ValueError:
            await message.answer("Noto'g'ri format! 2025-10-14 14:30 shaklida kiriting yoki '-':")
            return

    if created_at > datetime.now(TZ):
        await message.answer("🚫 Kelajakdagi vaqtni kiritib bo‘lmaydi.")
        return

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            await state.clear()
            return

        expense = Expense(user_id=user.id, amount=data["amount"], reason=data["reason"], created_at=created_at)
        session.add(expense)
        await session.commit()
        await session.refresh(expense)

    await message.answer(f"✅ Harajat saqlandi! ID: {expense.id}", reply_markup=get_expense_keyboard())
    await state.clear()

@router.message(F.text == "📋 Harajatlar ro'yxati")
async def list_expenses(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            return

        result = await session.execute(
            select(Expense).where(Expense.user_id == user.id).order_by(Expense.created_at.desc()).limit(50)
        )
        expenses = result.scalars().all()
        if not expenses:
            await message.answer("Hech qanday harajat yo'q.")
            return

        text = "📋 Harajatlar ro'yxati (eng yangilari birinchi):\n\n"
        for exp in expenses:
            text += f"ID: {exp.id} | Sana: {exp.created_at.strftime('%Y-%m-%d %H:%M')} | Summa: {exp.amount} so'm | Sabab: {exp.reason or 'Yo\'q'}\n"
        await message.answer(text, reply_markup=get_expense_keyboard())

# Delete expense
@router.message(F.text == "❌ Harajatni o'chirish")
async def delete_expense_start(message: types.Message, state: FSMContext):
    await message.answer("O'chirmoqchi bo'lgan harajat ID sini kiriting:")
    await state.set_state(DeleteExpense.id)

@router.message(DeleteExpense.id)
async def delete_expense_confirm(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    try:
        exp_id = int(message.text.strip())
        if exp_id <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Noto'g'ri ID! Musbat butun son kiriting.")
        return

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            await state.clear()
            return

        result = await session.execute(
            delete(Expense).where(Expense.user_id == user.id, Expense.id == exp_id)
        )
        await session.commit()

        if result.rowcount:
            await message.answer("✅ Harajat muvaffaqiyatli o'chirildi!")
        else:
            await message.answer("Bunday ID li harajat topilmadi.")

    await state.clear()
    await message.answer("Keyingi amal?", reply_markup=get_expense_keyboard())

# Expense statistics
@router.message(F.text == "📊 Harajatlar statistika")
async def expense_stats(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            return

        now = datetime.now(TZ)
        periods = {
            "Kunlik": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "Haftalik": (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            "Oylik": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "Yillik": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        }

        stats = {}
        for period, start in periods.items():
            result = await session.execute(
                select(func.sum(Expense.amount)).where(Expense.user_id == user.id, Expense.created_at >= start)
            )
            stats[period] = result.scalar() or 0

        text = "📊 Harajatlar statistikasi:\n\n"
        for k, v in stats.items():
            text += f"{k}: {v} so'm\n"

        text += "\nMaxsus davr uchun statistika: Boshlanish sanasini kiriting (YYYY-MM-DD) yoki '-' deb yozing (chiqish):"
        await message.answer(text)
        await state.set_state(CustomStats.start_date)

@router.message(CustomStats.start_date)
async def custom_stats(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    input_text = message.text.strip()

    if input_text == "-":
        await message.answer("Statistika bo'limidan chiqildi.", reply_markup=get_expense_keyboard())
        await state.clear()
        return

    try:
        start_date = datetime.strptime(input_text, "%Y-%m-%d")
        start_date = TZ.localize(start_date.replace(hour=0, minute=0, second=0, microsecond=0))
    except ValueError:
        await message.answer("Noto'g'ri format! YYYY-MM-DD shaklida kiriting yoki '-':")
        return

    now = datetime.now(TZ)
    if start_date > now:
        await message.answer("Boshlanish sanasi hozirgi vaqtdan keyin bo'lishi mumkin emas!")
        return

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            await state.clear()
            return

        result = await session.execute(
            select(func.sum(Expense.amount)).where(Expense.user_id == user.id, Expense.created_at >= start_date)
        )
        total = result.scalar() or 0

    await message.answer(f"{input_text} dan hozirgacha harajat: {total} so'm", reply_markup=get_expense_keyboard())
    await state.clear()

# Back to main menu
@router.message(F.text == "⬅️ Orqaga")
async def back_to_main_menu(message: types.Message):
    from app.handlers.start import show_main_menu
    await show_main_menu(message)