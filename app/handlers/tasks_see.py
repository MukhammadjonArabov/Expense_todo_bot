from aiogram import Router, types, F
from sqlalchemy import select, func
from app.database import async_session, PersonalTask
from app.addition.functions import get_user
from app.addition.task_fun import (
    get_years_keyboard,
    get_months_keyboard,
    get_task_type_keyboard,
    get_tasks_list,
    get_pagination_keyboard,
)

router = Router()


# 👁 Tugma bosilganda — yil ro‘yxatini chiqaradi
@router.message(F.text == "👁 Vazifalarni ko'rish")
async def show_task_years(message: types.Message):
    telegram_id = message.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)
    if not user:
        await message.answer("Avval ro‘yxatdan o‘ting! /start")
        return

    markup = await get_years_keyboard(user.id)
    if not markup:
        await message.answer("📭 Sizda hali hech qanday vazifa mavjud emas.")
        return

    await message.answer("📅 Vazifalarni ko‘rish uchun yilni tanlang:", reply_markup=markup)


# 📆 Yil bosilganda — shu yildagi oylarni chiqaradi
@router.callback_query(F.data.startswith("tasks_year:"))
async def show_task_months(callback: types.CallbackQuery):
    _, year = callback.data.split(":")
    year = int(year)
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)

    markup = await get_months_keyboard(user.id, year)
    if not markup:
        await callback.answer("Bu yilda vazifalar topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(f"🗓 {year}-yil uchun oy tanlang:", reply_markup=markup)
    await callback.answer()


# 📋 Oy bosilganda — Rejalar / Bajarilgan / Bajarilmagan bo‘limlari
@router.callback_query(F.data.startswith("tasks_month:"))
async def show_task_types(callback: types.CallbackQuery):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)

    markup = get_task_type_keyboard(year, month)
    await callback.message.edit_text(
        f"📆 <b>{year}-{month}</b> uchun bo‘limni tanlang:",
        reply_markup=markup,
        parse_mode="HTML"
    )
    await callback.answer()


# 📜 Tanlangan turdagi vazifalar (rejalar / bajarilgan / bajarilmagan)
@router.callback_query(F.data.startswith("tasks_type:"))
async def show_tasks_list(callback: types.CallbackQuery):
    _, t_type, year, month, page = callback.data.split(":")
    year, month, page = int(year), int(month), int(page)
    telegram_id = callback.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)

    tasks, total_pages = await get_tasks_list(user.id, year, month, t_type, page)

    if not tasks:
        await callback.message.edit_text("📭 Bu bo‘limda hech qanday vazifa yo‘q.", reply_markup=get_task_type_keyboard(year, month))
        await callback.answer()
        return

    text = f"📋 <b>{year}-{month}</b> oy uchun <b>{t_type.upper()}</b> vazifalar:\n\n"
    for t in tasks:
        status = "✅ Bajarilgan" if t.is_completed else "❌ Bajarilmagan"
        text += (
            f"📌 <b>{t.title}</b>\n"
            f"📝 {t.description or '—'}\n"
            f"📅 {t.deadline.strftime('%Y-%m-%d')}\n"
            f"{status}\n"
            f"──────────────\n"
        )

    markup = get_pagination_keyboard(year, month, t_type, page, total_pages)
    await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


# 🔙 Orqaga — yillar ro‘yxatiga qaytish
@router.callback_query(F.data == "back_to_task_years")
async def back_to_task_years(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        user = await get_user(session, telegram_id)

    markup = await get_years_keyboard(user.id)
    if not markup:
        await callback.message.edit_text("📭 Sizda hali hech qanday vazifa mavjud emas.")
        return

    await callback.message.edit_text("📅 Yilni tanlang:", reply_markup=markup)
    await callback.answer()
