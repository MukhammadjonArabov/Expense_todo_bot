from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime

from app.addition.functions import TZ, get_user
from app.addition.state import AddPersonalTask
from app.database import async_session, PersonalTask
from app.keyboards.expanse_main import show_main_menu
from app.keyboards.tasks_keyboard import (
    get_tasks_action_keyboard,
    get_personal_tasks_keyboard,
    get_cancel_keyboard
)
from app.addition.calendar_fun import (
    generate_years_keyboard,
    generate_months_keyboard,
    generate_days_keyboard
)

router = Router()

@router.message(F.text == "📝 Vazifalar")
async def show_task_menu(message: types.Message):
    await message.answer(
        "📝 Vazifalar bo‘limi:", reply_markup=await get_tasks_action_keyboard()
    )


@router.message(F.text == "👤 Shaxsiy")
async def show_personal_tasks_menu(message: types.Message):
    await message.answer(
        "👤 Shaxsiy vazifalar bo‘limi:", reply_markup=await get_personal_tasks_keyboard()
    )


@router.message(F.text == "➕ Vazifa qo‘shish")
async def add_task_start(message: types.Message, state: FSMContext):
    await message.answer(
        "✍️ Yangi vazifaning nomini kiriting:", reply_markup=await get_cancel_keyboard()
    )
    await state.set_state(AddPersonalTask.title)


@router.message(AddPersonalTask.title)
async def add_task_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer(
        "📅 Endi vazifa sanasini tanlang:", reply_markup=generate_years_keyboard()
    )
    await state.set_state(AddPersonalTask.month_day)


@router.callback_query(F.data.startswith("year:"))
async def choose_month(callback: types.CallbackQuery, state: FSMContext):
    year = int(callback.data.split(":")[1])
    await state.update_data(selected_year=year)
    await callback.message.edit_text(
        f"🗓 {year}-yil tanlandi. Endi oyni tanlang:",
        reply_markup=generate_months_keyboard(year)
    )


@router.callback_query(F.data.startswith("month:"))
async def choose_day(callback: types.CallbackQuery, state: FSMContext):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)
    await state.update_data(selected_month=month)
    await callback.message.edit_text(
        f"📆 {year}-yil {month}-oy tanlandi. Endi kunni tanlang:",
        reply_markup=generate_days_keyboard(year, month)
    )


@router.callback_query(F.data.startswith("day:"))
async def day_selected(callback: types.CallbackQuery, state: FSMContext):
    _, year, month, day = callback.data.split(":")
    selected_date = datetime(int(year), int(month), int(day), tzinfo=TZ)

    now = datetime.now(TZ)
    if selected_date.date() < now.date():
        await callback.answer("⚠️ O‘tgan kun tanlanmaydi!", show_alert=True)
        return

    await state.update_data(deadline=selected_date)
    await callback.message.edit_text(
        f"✅ Sana tanlandi: <b>{selected_date.strftime('%d-%m-%Y')}</b>\n\n"
        "Endi vazifa tavsifini kiriting (yoki 'yo‘q' deb yozing):",
        parse_mode="HTML"
    )
    await state.set_state(AddPersonalTask.description)


@router.message(AddPersonalTask.description)
async def add_task_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    deadline = data.get("deadline")

    if not title or not deadline:
        await message.answer(
            "⚠️ Ma’lumot yetarli emas, iltimos, boshqatdan boshlang!"
        )
        await state.clear()
        return

    description_text = message.text.strip()
    description = None if description_text.lower() in ["yo‘q", "yoq", "no", ""] else description_text

    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
        if not user:
            await message.answer(
                "⚠️ Avval ro‘yxatdan o‘ting! /start buyrug‘ini bosing."
            )
            await state.clear()
            return

        new_task = PersonalTask(
            title=title,
            description=description,
            deadline=deadline,
            user_id=user.id
        )
        session.add(new_task)
        await session.commit()

    await message.answer(
        "✅ Vazifa muvaffaqiyatli qo‘shildi!", reply_markup=await get_personal_tasks_keyboard()
    )
    await state.clear()


# ===== CANCEL HANDLERS =====
@router.message(F.text == "⬅️ Qaytish")
async def cancel_task_addition(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👇 Quyidagilardan birini tanlang:", reply_markup=await get_personal_tasks_keyboard()
    )


@router.message(F.text == "⬅️ Ortga qaytish")
async def come_back_task_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 Vazifalar menyusiga qaytdingiz!", reply_markup=await get_tasks_action_keyboard()
    )


@router.message(F.text == "🔙 Orqaga")
async def add_task_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz", reply_markup=await show_main_menu())


# ===== NAVIGATION CALLBACKS =====
@router.callback_query(F.data == "back_to_years")
async def back_to_years(callback: types.CallbackQuery):
    await callback.message.edit_text("📅 Yilni tanlang:", reply_markup=generate_years_keyboard())


@router.callback_query(F.data.startswith("back_to_months:"))
async def back_to_months(callback: types.CallbackQuery):
    year = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"🗓 {year}-yil uchun oyni tanlang:", reply_markup=generate_months_keyboard(year)
    )