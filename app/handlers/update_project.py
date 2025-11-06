import uuid
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import async_session, Project
from app.addition.functions import get_user
from app.addition.generate_invite import generate_invite_link
from app.keyboards.collective_keyboard import get_my_projects_menu
from app.addition.state import UpdateProject

router = Router()


# 🔘 O‘zgartirishni to‘xtatish tugmasi
async def cancel_update_button():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ O‘zgartirishni to‘xtatish")]],
        resize_keyboard=True
    )


# 🔘 Inline tugmalar orqali loyihalar ro‘yxatini chiqarish
async def get_user_projects_inline_keyboard(user_id: int):
    async with async_session() as session:
        projects = (
            await session.execute(
                select(Project).where(Project.create_by == user_id)
            )
        ).scalars().all()

    if not projects:
        return None

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p.name, callback_data=f"update_proj:{p.id}")]
            for p in projects
        ]
    )
    return keyboard


# 🛠 Loyihani o‘zgartirish menyusi
@router.message(F.text == "🛠 Loyihani o‘zgartirish")
async def choose_project_to_update(message: types.Message, state: FSMContext):
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)

        if not user:
            await message.answer("Siz tizimda ro‘yxatdan o‘tmagansiz.")
            return

        projects_keyboard = await get_user_projects_inline_keyboard(user.id)
        if not projects_keyboard:
            await message.answer(
                "❗ Siz hali birorta loyiha yaratmagansiz.",
                reply_markup=await get_my_projects_menu()
            )
            return

        await message.answer(
            "🛠 O‘zgartirmoqchi bo‘lgan loyihangizni tanlang:",
            reply_markup=projects_keyboard
        )
        await state.set_state(UpdateProject.select_project)


# 📂 Inline tugma orqali loyiha tanlanganda
@router.callback_query(F.data.startswith("update_proj:"))
async def start_project_update_callback(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        project = await session.get(Project, project_id)

    if not project:
        await callback.message.answer("❌ Loyiha topilmadi.")
        return

    await state.update_data(project_id=project.id)
    await callback.message.answer(
        f"✏️ Loyiha nomini yangilang yoki eski nomni qoldiring:\n\n"
        f"Joriy nom: <b>{project.name}</b>",
        parse_mode="HTML",
        reply_markup=await cancel_update_button()
    )
    await state.set_state(UpdateProject.new_name)
    await callback.answer()  # Inline yuklash animatsiyasini to‘xtatish


# ✏️ Yangi nomni olish
@router.message(UpdateProject.new_name)
async def get_new_project_name(message: types.Message, state: FSMContext):
    if message.text == "❌ O‘zgartirishni to‘xtatish":
        await state.clear()
        await message.answer(
            "🔙 O‘zgartirish bekor qilindi.",
            reply_markup=await get_my_projects_menu()
        )
        return

    new_name = message.text.strip()
    await state.update_data(new_name=new_name)
    await message.answer(
        "📜 Endi yangi tavsifni kiriting (yoki 'yo‘q' deb yozing):",
        reply_markup=await cancel_update_button()
    )
    await state.set_state(UpdateProject.new_description)


# 📝 Tavsifni olish va yangilash
@router.message(UpdateProject.new_description)
async def update_project_in_db(message: types.Message, state: FSMContext):
    if message.text == "❌ O‘zgartirishni to‘xtatish":
        await state.clear()
        await message.answer(
            "🔙 O‘zgartirish bekor qilindi.",
            reply_markup=await get_my_projects_menu()
        )
        return

    desc_text = message.text.strip().lower()
    new_desc = None if desc_text in ("yo‘q", "yoq", "yo'q") else message.text
    data = await state.get_data()
    project_id = data.get("project_id")
    new_name = data.get("new_name")

    async with async_session() as session:
        project = await session.get(Project, project_id)
        if not project:
            await message.answer("❗ Loyiha topilmadi.")
            return

        # 🔁 Yangi invite token va link yaratamiz
        new_invite_token = uuid.uuid4().hex
        new_invite_link = generate_invite_link(new_invite_token)

        project.name = new_name
        project.description = new_desc
        project.invite_token = new_invite_token
        project.invite_link = new_invite_link

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko‘ring.")
            return

    await message.answer(
        f"✅ Loyiha muvaffaqiyatli yangilandi!\n\n"
        f"📁 Yangi nom: <b>{new_name}</b>\n"
        f"📜 Tavsif: {new_desc or 'Yo‘q'}\n"
        f"🔗 Yangi taklif havolasi:\n{new_invite_link}\n\n"
        f"⚠️ Eski havola endi ishlamaydi.",
        parse_mode="HTML",
        reply_markup=await get_my_projects_menu()
    )
    await state.clear()
