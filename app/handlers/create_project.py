from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from app.config import BOT_USERNAME
import uuid
from app.addition.functions import get_user
from app.addition.state import CreateProject
from app.addition.generate_invite import generate_invite_link
from app.database import async_session, Project, User
from app.keyboards.collective_keyboard import get_my_projects_menu, get_team_menu

router = Router()


@router.message(F.text == "👥 Jamoviy")
async def show_collective_menu(message: types.Message):
    await message.answer(
        "Jamoviy bo‘limni tanlang 👇",
        reply_markup=await get_team_menu()
    )


@router.message(F.text == "📂 Mening loyhalarim")
async def show_my_projects_menu(message: types.Message):
    await message.answer(
        "Loyihalaringizni boshqarish uchun quyidagilardan birini tanlang 👇",
        reply_markup=await get_my_projects_menu()
    )


# ➕ 1-qadam: yangi loyiha yaratish jarayonini boshlash
@router.message(F.text == "➕ Yangi loyiha")
async def start_create_project(message: types.Message, state: FSMContext):
    await message.answer("🆕 Yangi loyihaning nomini kiriting:")
    await state.set_state(CreateProject.name)


# 2-qadam: loyiha nomini olish
@router.message(CreateProject.name)
async def get_project_name(message: types.Message, state: FSMContext):
    project_name = message.text.strip()

    if len(project_name) < 3:
        await message.answer("❗ Loyiha nomi juda qisqa. Kamida 3 ta belgidan iborat bo‘lsin.")
        return

    await state.update_data(name=project_name)
    await message.answer("✏️ Endi loyiha tavsifini kiriting (yoki 'yo‘q' deb yozing):")
    await state.set_state(CreateProject.description)


# 3-qadam: loyiha tavsifini olish va saqlash
@router.message(CreateProject.description)
async def get_project_description(message: types.Message, state: FSMContext):
    desc = None if message.text.lower() == "yo‘q" else message.text
    data = await state.get_data()
    telegram_id = message.from_user.id

    async with async_session() as session:
        # 🧩 Foydalanuvchini olish yoki yaratish
        user = await get_user(session, telegram_id)
        if not user:
            user = User(
                telegram_id=telegram_id,
                full_name=message.from_user.full_name,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()

        # 🔑 Taklif tokeni va havolasi
        invite_token = uuid.uuid4().hex
        invite_link = f"https://t.me/{BOT_USERNAME}?start={invite_token}"

        # 🏗 Yangi loyiha yaratish
        new_project = Project(
            name=data["name"],
            description=desc,
            create_by=user.id,
            invite_token=invite_token,
            invite_link=invite_link,
        )

        session.add(new_project)
        await session.commit()

        await message.answer(
            f"✅ Loyiha muvaffaqiyatli yaratildi!\n\n"
            f"📁 Nomi: <b>{new_project.name}</b>\n"
            f"🔗 Taklif havolasi:\n{new_project.invite_link}",
            parse_mode="HTML",
            reply_markup=await get_my_projects_menu(),
        )

    await state.clear()