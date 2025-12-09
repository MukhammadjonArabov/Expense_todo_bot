from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import async_session, User, Project, ProjectMember, RoleEnum
from app.keyboards.expanse_main import show_main_menu, phone_menu

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject, state: FSMContext):
    """
    /start yoki /start join_<token> ni qayta ishlaydi.
    1️⃣ Oddiy /start — ro‘yxatdan o‘tmagan bo‘lsa phone so‘raydi, bo‘lmasa menyu ko‘rsatadi.
    2️⃣ /start join_<token> — agar foydalanuvchi yo‘q bo‘lsa, tokenni saqlab, ro‘yxatdan o‘tish jarayoniga yo‘naltiradi.
    """
    args = command.args
    tg_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

        if not args:
            if user:
                await message.answer("🏠 Asosiy menyu:", reply_markup=await show_main_menu())
            else:
                await phone_menu(message)
            return

        if args.startswith("join_"):
            token = args.replace("join_", "")

            if not user:
                await state.update_data(pending_project_token=token)
                await phone_menu(message)
                return

            project_res = await session.execute(select(Project).where(Project.invite_token == token))
            project = project_res.scalars().first()
            if not project:
                await message.answer("❌ Taklif havolasi yaroqsiz yoki loyiha topilmadi.")
                return

            if user.id == project.create_by:
                await message.answer(
                    f"ℹ️ Siz <b>{project.name}</b> loyihasining egasisiz.",
                    parse_mode="HTML"
                )
                return

            member_check = await session.execute(
                select(ProjectMember).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.user_id == user.id
                )
            )
            member = member_check.scalars().first()
            if member:
                await message.answer(f"✅ Siz allaqachon <b>{project.name}</b> loyihasidasiz!", parse_mode="HTML")
                return

            new_member = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role=RoleEnum.member
            )
            session.add(new_member)
            await session.commit()

            await message.answer(
                f"🎉 Siz <b>{project.name}</b> loyihasiga muvaffaqiyatli qo‘shildingiz!",
                parse_mode="HTML",
                reply_markup=await show_main_menu()
            )


@router.message(F.contact)
async def contact_handler(message: types.Message, state: FSMContext):
    """
    Telefon yuborilganda foydalanuvchini ro‘yxatdan o‘tkazadi.
    Agar oldin token saqlangan bo‘lsa — uni loyiha a’zosi sifatida qo‘shadi.
    """
    contact = message.contact
    tg_id = message.from_user.id
    username = message.from_user.username
    user_link = f"https://t.me/{username}" if username else None
    phone = contact.phone_number

    async with async_session() as session:
        user = User(
            telegram_id=tg_id,
            username=username,
            user_link=user_link,
            phone=phone or ""
        )
        session.add(user)

        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("❗ Siz allaqachon ro'yxatdan o'tgansiz.")
            await message.answer("🏠 Asosiy menyu:", reply_markup=await show_main_menu())
            return

        data = await state.get_data()
        token = data.get("pending_project_token")

        if token:
            project_res = await session.execute(select(Project).where(Project.invite_token == token))
            project = project_res.scalars().first()

            if project:
                if user.id != project.create_by:
                    member = ProjectMember(
                        project_id=project.id,
                        user_id=user.id,
                        role=RoleEnum.member
                    )
                    session.add(member)
                    await session.commit()
                    await message.answer(
                        f"🎉 Siz <b>{project.name}</b> loyihasiga muvaffaqiyatli qo‘shildingiz!",
                        parse_mode="HTML"
                    )
                else:
                    await message.answer(
                        f"ℹ️ Siz <b>{project.name}</b> loyihasining egasisiz.",
                        parse_mode="HTML"
                    )
            await state.update_data(pending_project_token=None)

    await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=await show_main_menu())
