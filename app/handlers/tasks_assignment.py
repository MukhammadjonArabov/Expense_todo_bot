from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from datetime import datetime

from app.database import async_session, PersonalTask
from app.addition.functions import get_user, TZ
from app.keyboards.tasks_keyboard import get_cancel_keyboard, get_personal_tasks_keyboard

router = Router()

@router.message(F.text == "✍️ Bajarilganlarni belgilash")
async def mark_task_as_done(message: types.Message):
    telegram_id = message.from_user.id
    now = datetime.now(TZ).date()

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            await message.answer("Avval ro‘yxatdan o‘ting! /start")
            return

        result = await session.execute(
            select(PersonalTask).where(
                PersonalTask.user_id == user.id,
                PersonalTask.deadline == now
            )
        )
        tasks = result.scalars().all()

        if not tasks:
            await message.answer(
                "📅 Siz bugun uchun vazifalar kiritmagansiz.",
                reply_markup=await get_personal_tasks_keyboard()
            )
            return

        await message.answer("✍️ Bugungi vazifalaringiz:", reply_markup=await get_cancel_keyboard())

        for task in tasks:
            status = "✅ Bajarilgan" if task.is_completed else "❌ Bajarilmagan"
            text = (
                f"<b>🧠 Mavzu:</b> {task.title}\n\n"
                f"🕓 <b>Muddat:</b> {task.deadline}\n\n"
                f"⏳ <b>Holati:</b> {status}"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(text="✅ Bajardim", callback_data=f"done_{task.id}"),
                    InlineKeyboardButton(text="❌ Bajarmadim", callback_data=f"notdone_{task.id}")
                ]]
            )
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# ------------------ ✅ Bajardim tugmasi ------------------
@router.callback_query(F.data.startswith("done_"))
async def set_task_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    now = datetime.now(TZ).date()

    async with async_session() as session:
        task = await session.get(PersonalTask, task_id)

        if not task:
            await callback.answer("Vazifa topilmadi.", show_alert=True)
            return

        # ❗ Faqat bugungi vazifa o‘zgartiriladi
        if task.deadline != now:
            await callback.answer("⛔ Siz faqat bugungi vazifalarni o‘zgartira olasiz.", show_alert=True)
            return

        if not task.is_completed:
            task.is_completed = 1
            await session.commit()

        status = "✅ Bajarilgan"
        new_text = (
            f"<b>🧠 Mavzu:</b> {task.title}\n\n"
            f"🕓 <b>Muddat:</b> {task.deadline}\n\n"
            f"⏳ <b>Holati:</b> {status}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="✅ Bajardim", callback_data=f"done_{task.id}"),
                InlineKeyboardButton(text="❌ Bajarmadim", callback_data=f"notdone_{task.id}")
            ]]
        )

        await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("✅ Vazifa bajarilgan deb belgilandi.")

# ------------------ ❌ Bajarmadim tugmasi ------------------
@router.callback_query(F.data.startswith("notdone_"))
async def set_task_not_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    now = datetime.now(TZ).date()

    async with async_session() as session:
        task = await session.get(PersonalTask, task_id)

        if not task:
            await callback.answer("Vazifa topilmadi.", show_alert=True)
            return

        # ❗ Faqat bugungi vazifa o‘zgartiriladi
        if task.deadline != now:
            await callback.answer("⛔ Siz faqat bugungi vazifalarni o‘zgartira olasiz.", show_alert=True)
            return

        if task.is_completed:
            task.is_completed = 0
            await session.commit()

        status = "❌ Bajarilmagan"
        new_text = (
            f"<b>🧠 Mavzu:</b> {task.title}\n\n"
            f"🕓 <b>Muddat:</b> {task.deadline}\n\n"
            f"⏳ <b>Holati:</b> {status}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="✅ Bajardim", callback_data=f"done_{task.id}"),
                InlineKeyboardButton(text="❌ Bajarmadim", callback_data=f"notdone_{task.id}")
            ]]
        )

        await callback.message.edit_text(new_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("❌ Vazifa bajarilmagan deb belgilandi.")
