from aiogram import Router, types, F
from sqlalchemy import select, func
from datetime import datetime
from app.database import async_session, Expense
from app.addition.functions import get_user
from app.addition.keyboards import (
    get_statistics_action_keyboard,
    get_years_keyboard_statistic,
    get_months_keyboard_statistic
)
from app.addition.charts import generate_year_chart, generate_month_chart

TZ = datetime.now().astimezone().tzinfo  # vaqt mintaqasi
router = Router()


# =====================================================
# 📊 ASOSIY STATISTIKA — joriy oy uchun grafig bilan
# =====================================================
@router.message(F.text == "📊 Harajatlar statistika")
async def show_statistics_menu(message: types.Message):
    telegram_id = message.from_user.id
    now = datetime.now(TZ)
    year, month = now.year, now.month

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro‘yxatdan o‘ting! /start")
            return

        # 🔹 Shu oy bo‘yicha grafig
        result = await session.execute(
            select(
                func.extract('day', Expense.created_at).label('day'),
                func.sum(Expense.amount).label('total')
            )
            .where(
                (Expense.user_id == user.id)
                & (func.extract('year', Expense.created_at) == year)
                & (func.extract('month', Expense.created_at) == month)
            )
            .group_by('day')
            .order_by('day')
        )
        data = result.all()

        if data:
            chart = await generate_month_chart(year, month, data)
            total = sum(float(row[1]) for row in data)
            max_day, max_val = max(data, key=lambda x: x[1])
            min_day, min_val = min(data, key=lambda x: x[1])

            caption = (
                f"📊 {year}-{month}-oy statistikasi\n"
                f"💰 Umumiy: {int(total):,} so‘m\n"
                f"📈 Eng ko‘p: {int(max_day)}-kun ({int(max_val):,} so‘m)\n"
                f"📉 Eng kam: {int(min_day)}-kun ({int(min_val):,} so‘m)"
            )
            await message.answer_photo(photo=chart, caption=caption)
        else:
            await message.answer("📭 Bu oyda hech qanday harajat topilmadi.")

        await message.answer(
            "📊 Qaysi turdagi statistika kerak?",
            reply_markup=get_statistics_action_keyboard()
        )


# =====================================================
# 📅 YILLIK STATISTIKA
# =====================================================
@router.message(F.text == "📅 Yillik statistika")
async def show_years_list(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
        reply_markup = await get_years_keyboard_statistic(session, user.id)
        await message.answer("🗓 Yilni tanlang:", reply_markup=reply_markup)


@router.callback_query(F.data.startswith("choose_year_statistic:"))
async def show_selected_year_statistics(callback: types.CallbackQuery):
    _, user_id, year = callback.data.split(":")
    user_id, year = int(user_id), int(year)

    async with async_session() as session:
        result = await session.execute(
            select(
                func.extract('month', Expense.created_at).label('month'),
                func.sum(Expense.amount).label('total')
            )
            .where(
                (Expense.user_id == user_id)
                & (func.extract('year', Expense.created_at) == year)
            )
            .group_by('month')
            .order_by('month')
        )
        data = result.all()

        if not data:
            await callback.message.answer(f"📭 {year}-yilda harajat topilmadi.")
            await callback.answer()
            return

        chart = await generate_year_chart(year, data)
        total = sum(float(row[1]) for row in data)
        max_month, max_val = max(data, key=lambda x: x[1])
        min_month, min_val = min(data, key=lambda x: x[1])

        month_names = [
            "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
            "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
        ]

        caption = (
            f"📊 {year}-yil statistikasi\n"
            f"💰 Umumiy: {int(total):,} so‘m\n"
            f"📈 Eng ko‘p: {month_names[int(max_month)-1]} ({int(max_val):,} so‘m)\n"
            f"📉 Eng kam: {month_names[int(min_month)-1]} ({int(min_val):,} so‘m)"
        )

        await callback.message.answer_photo(photo=chart, caption=caption)
        await callback.answer()


# =====================================================
# 📆 OYLIK STATISTIKA
# =====================================================
@router.message(F.text == "📆 Oylik statistika")
async def show_years_for_monthly_stats(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)

        result = await session.execute(
            select(func.extract('year', Expense.created_at))
            .where(Expense.user_id == user.id)
            .distinct()
            .order_by(func.extract('year', Expense.created_at).desc())
        )
        years = [int(row[0]) for row in result.all()]

    keyboard = [
        [types.InlineKeyboardButton(
            text=f"📆 {year}",
            callback_data=f"choose_year_stat:{user.id}:{year}"
        )] for year in years
    ]
    markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("🗓 Qaysi yil uchun statistikani ko‘rmoqchisiz?", reply_markup=markup)


@router.callback_query(F.data.startswith("choose_year_stat:"))
async def show_months_for_selected_year(callback: types.CallbackQuery):
    _, user_id, year = callback.data.split(":")
    user_id, year = int(user_id), int(year)

    async with async_session() as session:
        result = await session.execute(
            select(func.extract('month', Expense.created_at))
            .where(
                (Expense.user_id == user_id)
                & (func.extract('year', Expense.created_at) == year)
            )
            .distinct()
            .order_by(func.extract('month', Expense.created_at))
        )
        months = [int(row[0]) for row in result.all()]

    if not months:
        await callback.message.edit_text(f"{year}-yilda hech qanday harajat topilmadi.")
        await callback.answer()
        return

    markup = get_months_keyboard_statistic(year, months)
    await callback.message.edit_text(f"📆 {year}-yil uchun oy tanlang:", reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("choose_month_statistic:"))
async def show_month_chart(callback: types.CallbackQuery):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)

        result = await session.execute(
            select(
                func.extract('day', Expense.created_at).label('day'),
                func.sum(Expense.amount).label('total')
            )
            .where(
                (Expense.user_id == user.id)
                & (func.extract('year', Expense.created_at) == year)
                & (func.extract('month', Expense.created_at) == month)
            )
            .group_by('day')
            .order_by('day')
        )
        data = result.all()

        if not data:
            await callback.message.answer("Bu oyda hech qanday harajat topilmadi.")
            await callback.answer()
            return

        chart = await generate_month_chart(year, month, data)
        total = sum(float(row[1]) for row in data)
        max_day, max_val = max(data, key=lambda x: x[1])
        min_day, min_val = min(data, key=lambda x: x[1])

        caption = (
            f"📊 {year}-{month}-oy statistikasi\n"
            f"💰 Umumiy: {int(total):,} so‘m\n"
            f"📈 Eng ko‘p: {int(max_day)}-kun ({int(max_val):,} so‘m)\n"
            f"📉 Eng kam: {int(min_day)}-kun ({int(min_val):,} so‘m)"
        )
        await callback.message.answer_photo(photo=chart, caption=caption)
        await callback.answer()
