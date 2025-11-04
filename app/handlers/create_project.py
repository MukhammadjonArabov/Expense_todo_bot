import uuid
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import async_session, Project, User, ProjectMember, RoleEnum
from app.addition.functions import get_user
from app.addition.generate_invite import generate_invite_link
from app.keyboards.collective_keyboard import get_my_projects_menu, get_team_menu, cancel_button
from app.addition.state import CreateProject

router = Router()


@router.message(lambda m: "jamoviy" in m.text.lower().replace("\u00A0", " "))
async def show_collective_menu(message: types.Message):
    await message.answer("Jamoviy bo‘limni tanlang 👇", reply_markup=await get_team_menu())

@router.message(F.text == "📂 Mening loyhalarim")
async def show_my_projects_menu(message: types.Message):
    await message.answer(
        "Loyihalaringizni boshqarish uchun quyidagilardan birini tanlang 👇",
        reply_markup=await get_my_projects_menu()
    )

@router.message(F.text == "➕ Yangi loyiha")
async def start_create_project(message: types.Message, state: FSMContext):
    await message.answer(
        "🆕 Yangi loyihaning nomini kiriting yoki '❌ Bekor qilish' tugmasini bosing:",
        reply_markup=await cancel_button()
    )
    await state.set_state(CreateProject.name)


@router.message(CreateProject.name, F.text.casefold() == "❌ bekor qilish".casefold())
@router.message(CreateProject.description, F.text.casefold() == "❌ bekor qilish".casefold())
async def cancel_create_project(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Loyiha yaratish bekor qilindi.",
        reply_markup=await get_my_projects_menu()
    )


@router.message(CreateProject.name)
async def get_project_name(message: types.Message, state: FSMContext):
    project_name = message.text.strip()

    if len(project_name) < 3:
        await message.answer("❗ Loyiha nomi juda qisqa. Kamida 3 ta belgidan iborat bo‘lsin.")
        return

    await state.update_data(name=project_name)
    await message.answer(
        "✏️ Endi loyiha tavsifini kiriting (yoki 'yo‘q' deb yozing):",
        reply_markup=await cancel_button()
    )
    await state.set_state(CreateProject.description)


@router.message(CreateProject.description)
async def get_project_description(message: types.Message, state: FSMContext):
    desc_text = message.text.strip().lower()
    desc = None if desc_text in ("yo‘q", "yoq", "yo'q", "yoq.") else message.text
    data = await state.get_data()
    telegram_id = message.from_user.id

    async with async_session() as session:
        user = await get_user(session, telegram_id)
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=message.from_user.username,
                user_link=f"https://t.me/{message.from_user.username}" if message.from_user.username else None,
                phone=""
            )
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                user = await get_user(session, telegram_id)

        invite_token = uuid.uuid4().hex
        invite_link = generate_invite_link(invite_token)

        new_project = Project(
            name=data["name"],
            description=desc,
            create_by=user.id,
            invite_token=invite_token,
            invite_link=invite_link,
        )
        session.add(new_project)
        await session.commit()

        owner_member = ProjectMember(
            project_id=new_project.id,
            user_id=user.id,
            role=RoleEnum.owner
        )
        session.add(owner_member)
        await session.commit()

        await message.answer(
            f"✅ Loyiha muvaffaqiyatli yaratildi!\n\n"
            f"📁 Nomi: <b>{new_project.name}</b>\n"
            f"🔗 Taklif havolasi:\n{new_project.invite_link}",
            parse_mode="HTML",
            reply_markup=await get_my_projects_menu()
        )

    await state.clear()

@router.message(F.text == "🔙 Ortga")
async def back_team_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Loyhalar menyuga qaytdingiz",
        reply_markup=await get_team_menu()
    )