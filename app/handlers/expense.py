from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.addition.functions import show_expenses_page, AddExpense, TZ, DeleteExpense, show_expense_statistics
from app.addition.inline import get_expense_keyboard, get_expenses_action_keyboard, get_years_keyboard, \
    get_months_keyboard
from app.database import async_session, Expense, User
from sqlalchemy import select, func
from datetime import datetime, timedelta

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
        telegram_id = message.from_user.id
        async with async_session() as session:
            user = await get_user(session, telegram_id)
            if not user:
                await message.answer("Avval ro'yxatdan o'ting! /start")
                return
            await show_expense_statistics(message, session, user.id)

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
        await message.answer("Harajat sababini kiriting\n"
                             "Agar besabab bo'lsa - belgini kiriting!")
        await state.set_state(AddExpense.reason)
    except ValueError:
        await message.answer("Iltimos, to'g'ri musbat butun son kiriting!")

@router.message(AddExpense.reason)
async def add_expense_reason(message: types.Message, state: FSMContext):
    reason = message.text.strip() if message.text.strip() != "-" else None
    await state.update_data(reason=reason)
    await message.answer("Sana va vaqtni kiriting masalan: 2025-10-14 14:30"
                         "\nhozirgi vaqtni kiritish uchun - belgini kiritng!")
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
############################################################################################################

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
async def change_expense_page(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await callback.answer("Avval ro'yxatdan o'ting!", show_alert=True)
            return
        await show_expenses_page(callback.message, session, user.id, page=page, edit=True)
    await callback.answer()

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
##################################################################################


# 📋 Default — o'tgan va hozirgi oy
@router.message(F.text == "📋 Harajatlar ro'yxati")
async def show_default_expenses(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            return

        now = datetime.now(TZ)
        current_year, current_month = now.year, now.month

        prev_month_date = now.replace(day=1) - timedelta(days=1)
        prev_year, prev_month = prev_month_date.year, prev_month_date.month

        # Hozirgi oy harajatlarini ko‘rsatish
        await show_expenses_page(
            target=message,
            session=session,
            user_id=user.id,
            page=1,
            year=current_year,
            month=current_month,
        )

        # ⚠️ E’tibor: Bu joyda keyboard chiqishi uchun reply_markup shunday chaqiriladi
        await message.answer(
            "👇 Quyidagi harakatlardan birini tanlang:",
            reply_markup=get_expenses_action_keyboard()
        )


# 📆 “Yil va oy bo‘yicha ko‘rish” tugmasi
@router.message(F.text == "📆 Yil va oy bo‘yicha ko‘rish")
async def choose_expense_year(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro'yxatdan o'ting! /start")
            return

        # Foydalanuvchining mavjud yillarini olish
        result = await session.execute(
            select(func.extract('year', Expense.created_at))
            .where(Expense.user_id == user.id)
            .distinct()
            .order_by(func.extract('year', Expense.created_at).desc())
        )
        years = [int(row[0]) for row in result.all()]

        if not years:
            await message.answer("Hech qanday harajat topilmadi.")
            return

        # Agar faqat bitta yil (joriy yil) bo‘lsa → to‘g‘ridan-to‘g‘ri oy tanlash
        if len(years) == 1 and years[0] == datetime.now(TZ).year:
            await show_months_for_year(message, user.id, years[0])
            return

        # Aks holda yil tanlash
        await message.answer("🗓 Yilni tanlang:", reply_markup=get_years_keyboard(years, user.id))


# 🔘 Yil bosilganda — oylik tanlash
@router.callback_query(F.data.startswith("choose_year:"))
async def choose_month_by_year(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    user_id = int(parts[1])
    year = int(parts[2])
    await show_months_for_year(callback.message, user_id, year, edit=True)


async def show_months_for_year(target, user_id: int, year: int, edit=False):
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
        if isinstance(target, types.Message):
            await target.answer("Bu yil uchun hech qanday harajat topilmadi.")
        else:
            await target.answer("Bu yil uchun hech qanday harajat topilmadi.", show_alert=True)
        return

    text = f"📅 {year}-yil uchun oyni tanlang:"
    markup = get_months_keyboard(year, months)

    if edit:
        await target.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)


# 🔙 Orqaga — yil ro‘yxatiga qaytish
@router.callback_query(F.data == "back_to_years")
async def back_to_years(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        result = await session.execute(
            select(func.extract('year', Expense.created_at))
            .where(Expense.user_id == user.id)
            .distinct()
            .order_by(func.extract('year', Expense.created_at).desc())
        )
        years = [int(row[0]) for row in result.all()]
    markup = get_years_keyboard(years, user.id)
    await callback.message.edit_text("🗓 Yilni tanlang:", reply_markup=markup)


# 📆 OY bosilganda — harajatlarni chiqarish
@router.callback_query(F.data.startswith("choose_month:"))
async def show_expenses_by_month(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    year = int(parts[1])
    month = int(parts[2])
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        await show_expenses_page(
            target=callback.message,
            session=session,
            user_id=user.id,
            page=1,
            year=year,
            month=month,
            edit=True
        )

##################################################################################################################

@router.message(F.text == "📊 Harajatlar statistika")
async def handle_statistics(message, state):
    user_id = message.from_user.id
    async with async_session() as session:
        await show_expense_statistics(message, session, user_id)

