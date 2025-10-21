from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.addition.functions import get_task_statistics
from app.keyboards.tasks_keyboard import get_personal_tasks_keyboard

from app.keyboards.tasks_keyboard import get_tasks_list_keyboard

router = Router()

@router.message(F.text == "📋 Vazifalar ro‘yxati")
async def show_tasks_list(message: types.Message):
    stats = await get_task_statistics(message.from_user.id)

    text = (
        f"📊 <b>Vazifalar statistikasi:</b>\n\n"
        f"🔹 Jami vazifalar: {stats['total']}\n\n"
        f"✅ Bajarilganlar: {stats['completed']}\n\n"
        f"❌ Bajarilmaganlar: {stats['not_completed']}\n\n"
        f"⏳ Bajarish kutilayotganlar: {stats['upcoming']}"
    )

    await message.answer(text, parse_mode="HTML")
    await message.answer(
        "👇 Quyidagi harakatlardan birini tanlang:",
        reply_markup=await get_tasks_list_keyboard()
    )


@router.message(F.text == "⬅️ Ortga")
async def show_tasks_back_down(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👇 Quyidagi harakatlardan birini tanlang",
                         reply_markup=await get_personal_tasks_keyboard())