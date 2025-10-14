from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.addition.functions import show_expenses_page, AddExpense, TZ, DeleteExpense
from app.addition.inline import get_expense_keyboard
from app.database import async_session, Expense, User
from sqlalchemy import select, delete, func
from datetime import datetime, timedelta
from aiogram.fsm.state import State, StatesGroup

from app.handlers.start import show_main_menu

router = Router()

async def get_user(session, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()

@router.message(F.text.contains("Harajatlar"))
async def expense_menu(message: types.Message):
    text = message.text

    if text == "📋 Harajatlar ro'yxati":
        telegram_id = message.from_user.id
        async with async_session() as session:
            user = await get_user(session, telegram_id)
            if not user:
                await message.answer("Avval ro'yxatdan o'ting! /start")
                return
            await show_expenses_page(message, session, user.id, page=1)

    elif text == "➕ Harajat qo'shish":
        await message.answer("📝 Yangi harajat qo‘shish uchun summa va sababni kiriting...")

    elif text == "📊 Harajatlar statistika":
        await message.answer("📊 Statistikani hozircha tayyorlayapmiz...")

    elif text == "⬅️ Orqaga":
        await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=show_main_menu())

    else:
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
                         "\nhozirgi vaqtni belgilash uchun - belgini kiritng!")
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
        await show_expenses_page(message, session, user.id, page=1)

@router.callback_query(F.data.startswith("expenses_page:"))
async def paginate_expenses(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await callback.answer("Avval ro'yxatdan o'ting! /start", show_alert=True)
            return

        await show_expenses_page(callback, session, user.id, page)

@router.message(F.text == "🗑 O'chirish")
async def ask_delete_id(message: types.Message, state: FSMContext):
    await message.answer("🗑 O‘chirmoqchi bo‘lgan harajat ID raqamini kiriting:")
    await state.set_state(DeleteExpense.waiting_for_id)

@router.message(F.text == "🔙 Menyuga qaytish")
async def back_to_menu(message: types.Message):
    await message.answer("📋 Harajatlar menyuga qaytdingiz.", reply_markup=get_expense_keyboard())


@router.message(DeleteExpense.waiting_for_id)
async def delete_expense_by_id(message: types.Message, state: FSMContext):
    try:
        expense_id = int(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, to‘g‘ri ID raqamini kiriting.")
        return

    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            await state.clear()
            return

        result = await session.execute(
            select(Expense).where(Expense.id == expense_id, Expense.user_id == user.id)
        )
        expense = result.scalar_one_or_none()
        if not expense:
            await message.answer("❌ Bunday ID sizning harajatlaringiz orasida topilmadi.")
            await state.clear()
            return

        await session.delete(expense)
        await session.commit()

        await message.answer(f"✅ Harajat o‘chirildi (ID: {expense_id}).")
        await state.clear()
