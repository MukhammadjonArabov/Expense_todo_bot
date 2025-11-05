from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import calendar

from app.addition.calendar_fun import cal_generate_years, cal_generate_days, cal_generate_months
from app.addition.functions import TZ, get_user
from app.addition.state import AddExpense
from app.database import async_session, Expense
from app.keyboards.expanse_main import get_expense_keyboard, get_back_keyboard

router = Router()


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
        reply_markup=cal_generate_years()
    )
    await state.set_state(AddExpense.date)


# ===== INLINE CALENDAR CALLBACKS =====
@router.callback_query(F.data.startswith("cal_year:"))
async def process_cal_year(callback: types.CallbackQuery, state: FSMContext):
    _, year = callback.data.split(":")
    year = int(year)
    await state.update_data(selected_year=year)
    await callback.message.edit_text(
        f"📅 {year}-yil tanlandi. Endi oyni tanlang:",
        reply_markup=cal_generate_months(year)
    )


@router.callback_query(F.data.startswith("cal_month:"))
async def process_cal_month(callback: types.CallbackQuery, state: FSMContext):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)
    await state.update_data(selected_month=month)
    await callback.message.edit_text(
        f"📅 {year}-yil, {month}-oy tanlandi. Endi kunni tanlang:",
        reply_markup=cal_generate_days(year, month)
    )


@router.callback_query(F.data.startswith("cal_day:"))
async def process_cal_day(callback: types.CallbackQuery, state: FSMContext):
    _, year, month, day = callback.data.split(":")
    selected_date = datetime(int(year), int(month), int(day), tzinfo=TZ).date()
    now = datetime.now(TZ).date()

    if selected_date > now:
        await callback.answer("⚠️ Kelajak sanasini tanlab bo‘lmaydi!", show_alert=True)
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
            created_at=selected_date  # soatsiz sana
        )
        session.add(expense)
        await session.commit()
        await session.refresh(expense)

    await callback.message.answer(
        f"✅ Harajat muvaffaqiyatli saqlandi!\n\n"
        f"🆔 ID: {expense.id}\n"
        f"💰 Miqdor: {expense.amount}\n"
        f"📝 Sabab: {expense.reason or 'Noma’lum'}\n"
        f"📅 Sana: {expense.created_at}",
        reply_markup=get_expense_keyboard()
    )
    await state.clear()


# ===== NAVIGATION CALLBACKS =====
@router.callback_query(F.data == "cal_back_to_years")
async def back_to_years(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📅 Yilni tanlang:", reply_markup=cal_generate_years()
    )


@router.callback_query(F.data.startswith("cal_back_to_months:"))
async def back_to_months(callback: types.CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"📅 {year}-yil uchun oyni tanlang:", reply_markup=cal_generate_months(year)
    )
