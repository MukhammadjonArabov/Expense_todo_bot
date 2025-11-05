from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.addition.functions import show_expenses_page, TZ, get_user, cancel_adding_expense
from app.addition.state import AddExpense, DeleteExpense
from app.database import async_session, Expense
from sqlalchemy import select, func
from datetime import datetime

from app.handlers.statistics import show_statistics_menu
from app.keyboards.expanse_main import get_expense_keyboard, show_main_menu, get_back_keyboard, \
    get_expenses_action_keyboard, get_months_keyboard, get_years_keyboard
from app.addition.calendar_fun import (
    generate_years_keyboard,
    generate_months_keyboard,
    generate_days_keyboard
)

router = Router()



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
        await add_expense_start(message)

    elif text == "📊 Harajatlar statistika":
        await show_statistics_menu(message)

    elif text == "⬅️ Orqaga":
        await back_to_home_menu(message)

    else:
        await message.answer(
            "💰 Harajatlar bo'limiga o'tdingiz. Quyidagilardan birini tanlang:",
            reply_markup=get_expense_keyboard()
        )

@router.message(F.text == "⬅️ Orqaga")
async def back_to_home_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz!", reply_markup= await show_main_menu())


async def cancel_adding_expense(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔙 Harajat qo‘shish bekor qilindi.",
        reply_markup=get_expense_keyboard()
    )


@router.message(F.text == "➕ Harajat qo'shish")
async def add_expense_start(message: types.Message, state: FSMContext):
    await message.answer(
        "💰 Harajat summasini kiriting (faqat musbat butun son):",
        reply_markup=await get_back_keyboard()
    )
    await state.set_state(AddExpense.amount)


@router.message(AddExpense.amount)
async def add_expense_amount(message: types.Message, state: FSMContext):
    if message.text.strip() == "🔙 Menyuga qaytish":
        await cancel_adding_expense(message, state)
        return

    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("🚫 Iltimos, musbat butun son kiriting!")
        return

    await state.update_data(amount=amount)
    await message.answer(
        "📝 Harajat sababini kiriting (yoki '-' kiriting):",
        reply_markup=await get_back_keyboard()
    )
    await state.set_state(AddExpense.reason)


@router.message(AddExpense.reason)
async def add_expense_reason(message: types.Message, state: FSMContext):
    if message.text.strip() == "🔙 Menyuga qaytish":
        await cancel_adding_expense(message, state)
        return

    reason = message.text.strip()
    reason = None if reason == "-" else reason
    await state.update_data(reason=reason)

    await message.answer(
        "📅 Harajat sanasini tanlang: \nAvvalo yilni tanlang",
        reply_markup=generate_years_keyboard()
    )
    await state.set_state(AddExpense.date)


# --- Inline keyboard bilan yil/oy/kun tanlash

# 4.1 Yilni tanlash
@router.callback_query(F.data.startswith("year:"))
async def process_year(callback: types.CallbackQuery, state: FSMContext):
    _, year = callback.data.split(":")
    year = int(year)
    await state.update_data(selected_year=year)
    await callback.message.edit_text(
        f"📅 {year}-yil tanlandi. Endi oyni tanlang:",
        reply_markup=generate_months_keyboard(year)
    )


# 4.2 Oyni tanlash
@router.callback_query(F.data.startswith("month:"))
async def process_month(callback: types.CallbackQuery, state: FSMContext):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)
    await state.update_data(selected_month=month)
    await callback.message.edit_text(
        f"📅 {year}-yil, {month}-oy tanlandi. Endi kunni tanlang:",
        reply_markup=generate_days_keyboard(year, month)
    )


# 4.3 Kunni tanlash
@router.callback_query(F.data.startswith("day:"))
async def process_day(callback: types.CallbackQuery, state: FSMContext):
    _, year, month, day = callback.data.split(":")
    selected_date = datetime(int(year), int(month), int(day), tzinfo=TZ)

    # O‘tgan sanani tekshirish
    now = datetime.now(TZ)
    if selected_date.date() < now.date():
        await callback.answer("⚠️ O‘tgan sana tanlanmaydi!", show_alert=True)
        return

    await state.update_data(selected_date=selected_date)

    data = await state.get_data()
    amount = data.get("amount")
    reason = data.get("reason")

    if amount is None:
        await callback.message.answer("⚠️ Miqdor topilmadi. Iltimos, boshqatdan boshlang!")
        await state.clear()
        return

    async with async_session() as session:
        user = await get_user(session, callback.from_user.id)
        if not user:
            await callback.message.answer("❗ Avval ro‘yxatdan o‘ting! /start")
            await state.clear()
            return

        expense = Expense(
            user_id=user.id,
            amount=amount,
            reason=reason,
            created_at=selected_date
        )
        session.add(expense)
        await session.commit()
        await session.refresh(expense)

    await callback.message.answer(
        f"✅ Harajat muvaffaqiyatli saqlandi!\n\n"
        f"🆔 ID: {expense.id}\n"
        f"💰 Miqdor: {expense.amount}\n"
        f"📝 Sabab: {expense.reason or 'Noma’lum'}\n"
        f"📅 Sana: {expense.created_at.astimezone(TZ).strftime('%Y-%m-%d')}",
        reply_markup=get_expense_keyboard()
    )
    await state.clear()


@router.callback_query(F.data == "back_to_years")
async def back_to_years(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📅 Yilni tanlang:",
        reply_markup=generate_years_keyboard()
    )


@router.callback_query(F.data.startswith("back_to_months:"))
async def back_to_months(callback: types.CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"📅 {year}-yil uchun oyni tanlang:",
        reply_markup=generate_months_keyboard(year)
    )
async def cancel_adding_expense(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔙 Harajat qo‘shish bekor qilindi.",
        reply_markup=get_expense_keyboard()
    )

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


# Default — o'tgan va hozirgi oy
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
            select(
                func.extract('year', Expense.created_at)
            ).where(
                Expense.user_id == user.id
            ).distinct().order_by(
                func.extract('year', Expense.created_at).desc()
            )

        )
        years = [int(row[0]) for row in result.all()] # barcha yillarni listga yi'g'ish

        if not years:
            await message.answer("Hech qanday harajat topilmadi.")
            return

        # Agar faqat bitta yil (joriy yil) bo‘lsa → to‘g‘ridan-to‘g‘ri oy tanlash
        if len(years) == 1 and years[0] == datetime.now(TZ).year:
            await show_months_for_year(message, user.id, years[0])
            return

        # Aks holda yil tanlash
        await message.answer("🗓 Yilni tanlang:", reply_markup=get_years_keyboard(years, user.id))


# Yil bosilganda — oylik tanlash
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


#Orqaga — yil ro‘yxatiga qaytish
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


#OY bosilganda — harajatlarni chiqarish
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

