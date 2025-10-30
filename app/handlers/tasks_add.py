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

router = Router()

@router.message(F.text == "📝 Vazifalar")
async def show_task_menu(message: types.Message):
    await message.answer(
        "📝 Vazifalar bo‘limi:",
        reply_markup=await get_tasks_action_keyboard()
    )


@router.message(F.text == "👤 Shaxsiy")
async def show_personal_tasks_menu(message: types.Message):
    await message.answer(
        "👤 Shaxsiy vazifalar bo‘limi:",
        reply_markup=await get_personal_tasks_keyboard()
    )


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
        "👇 Quyidagilardan birini tanlang:",
        reply_markup=await get_personal_tasks_keyboard()
    )


@router.message(F.text == "⬅️ Ortga qaytish")
async def come_back_task_manu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 Vazifalar menyusiga qaytdingiz!",
        reply_markup=await get_tasks_action_keyboard()
    )


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
        selected_date = datetime(year, month, day, tzinfo=TZ)

        if selected_date.date() < now.date():
            await message.answer("⚠️ O‘tgan sana tanlanmaydi! Boshqatdan kiriting:")
            return

        await state.update_data(deadline=selected_date)
        await message.answer(
            "📄 Vazifa tavsifini kiriting (yoki 'yo‘q' deb yozing):",
            reply_markup=await get_cancel_keyboard()
        )
        await state.set_state(AddPersonalTask.description)

    except Exception:
        await message.answer("❌ Sana noto‘g‘ri formatda. Masalan: `12-31`")


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

    await message.answer(
        "✅ Vazifa muvaffaqiyatli qo‘shildi!",
        reply_markup=await get_personal_tasks_keyboard()
    )
    await state.clear()


@router.message(F.text == "🔙 Orqaga")
async def add_task_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz",
        reply_markup=await show_main_menu()
    )
