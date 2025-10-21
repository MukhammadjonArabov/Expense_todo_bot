from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
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
        "✍️ Yangi vazifaning nomini kiriting:\n\n"
        "❌ To‘xtatish — jarayonni bekor qiladi.",
        reply_markup=await get_cancel_keyboard()
    )
    await state.set_state(AddPersonalTask.title)

@router.message(F.text == "❌ To‘xtatish")
async def cancel_task_addition(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Vazifa qo‘shish bekor qilindi.", reply_markup= await get_personal_tasks_keyboard())

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
async def add_task_month_day(message: types.Message, state: FSMContext):
    text = message.text.strip()
    now = datetime.now(TZ)
    year = now.year

    try:
        month, day = map(int, text.split("-"))
        deadline = datetime(year, month, day, tzinfo=TZ)
    except ValueError:
        await message.answer("❌ Noto‘g‘ri format! Masalan: `12-31` (oy-kun)")
        return

    if deadline.date() < now.date():
        await message.answer("⚠️ O‘tgan sana uchun vazifa qo‘ya olmaysiz! Bugundan keyingi kunni kiriting.")
        return

    await state.update_data(deadline=deadline)
    await message.answer(
        "📝 Vazifaning tavsifini kiriting yoki 'yo‘q' deb yozing.",
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