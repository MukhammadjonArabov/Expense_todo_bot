from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

from app.addition.calendar import generate_month_days_keyboard
from app.addition.functions import TZ, get_user
from app.addition.state import AddPersonalTask
from app.database import async_session, Task, PersonalTask
from app.keyboards.expanse_main import show_main_menu
from app.keyboards.tasks_keyboard import (
   get_tasks_action_keyboard,
   get_personal_tasks_keyboard,
   get_cancel_keyboard
)

router = Router()

@router.message(F.text == "📝 Vazifalar")
async def show_task_menu(message: types.Message):
    await message.answer("📝 Vazifalar bo‘limi:", reply_markup= await get_tasks_action_keyboard())


@router.message(F.text == "👤 Shaxsiy")
async def show_personal_tasks_menu(message: types.Message):
    await message.answer("👤 Shaxsiy vazifalar bo‘limi:", reply_markup= await get_personal_tasks_keyboard())

@router.message(F.text == "➕ Vazifa qo‘shish")
async def add_task_start(message: types.Message, state: FSMContext):
    await message.answer(
        "✍️ Yangi vazifaning nomini kiriting:",
        reply_markup=await get_cancel_keyboard()
    )
    await state.set_state(AddPersonalTask.title)

@router.message(F.text == "⬅️ Qaytish")
async def cancel_task_addition(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👇 Quydagilardan birini tanlang",
        reply_markup= await get_personal_tasks_keyboard()
    )

@router.message(F.text == "⬅️ Ortga qaytish")
async def come_back_task_manu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("📝 Vazifalar menyusiga qaytdingiz!", reply_markup=await get_tasks_action_keyboard())

@router.message(AddPersonalTask.title)
async def add_task_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "📅 Vazifa sanasini kiriting (oy-kun), masalan: `12-31`",
        reply_markup=await get_cancel_keyboard()
    )
    await state.set_state(AddPersonalTask.month_day)

@router.message(AddPersonalTask.month_day)
async def choose_date(message: types.Message, state: FSMContext):
    now = datetime.now(TZ)
    await message.answer(
        "📅 Oy va kunni tanlang:",
        reply_markup=generate_month_days_keyboard(now.year, now.month)
    )

@router.callback_query(F.data.startswith("change_month"))
async def change_month(callback: types.CallbackQuery):
    _, date_str = callback.data.split(":")
    year, month = map(int, date_str.split("-"))
    await callback.message.edit_reply_markup(reply_markup=generate_month_days_keyboard(year, month))

@router.callback_query(F.data.startswith("pick_date"))
async def pick_date(callback: types.CallbackQuery, state: FSMContext):
    _, date_str = callback.data.split(":")
    year, month, day = map(int, date_str.split("-"))
    selected_date = datetime(year, month, day, tzinfo=TZ)
    now = datetime.now(TZ)

    if selected_date.date() < now.date():
        await callback.answer("⚠️ O‘tgan sana tanlanmaydi!", show_alert=True)
        return

    await state.update_data(deadline=selected_date)
    await callback.message.edit_text(
        f"🗓 Sana: {selected_date.strftime('%Y-%m-%d')}\n\n"
        f"📝 Endi vazifa tavsifini kiriting (yoki 'yo‘q' deb yozing):",
        reply_markup=await get_cancel_keyboard()
    )
    await state.set_state(AddPersonalTask.description)
@router.message(AddPersonalTask.description)
async def add_task_description(message: types.Message, state: FSMContext):
    text = message.text.strip()
    description = None if text.lower() in ["yo‘q", "yoq", "no", ""] else text
    data = await state.get_data()

    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
        if not user:
            await message.answer("⚠️ Avval ro‘yxatdan o‘ting! /start buyrug‘ini bosing.")
            await state.clear()
            return

        new_task = PersonalTask(
            title=data["title"],
            description=description,
            deadline=data["deadline"],
            user_id=user.id
        )

        session.add(new_task)
        await session.commit()

    await message.answer("✅ Vazifa muvaffaqiyatli qo‘shildi!", reply_markup= await get_personal_tasks_keyboard())
    await state.clear()

@router.message(F.text == "🔙 Orqaga")
async def add_task_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosoiy menyuga qaytdingiz", reply_markup=await show_main_menu())