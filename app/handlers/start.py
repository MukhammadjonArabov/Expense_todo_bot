from aiogram import Router, types, F
from aiogram.filters import Command

from app.keyboards.expanse_main import show_main_menu, phone_menu
from app.database import async_session, User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    tg_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

    if user:
        keyboard = await show_main_menu()
        await message.answer("🏠 Asosiy menyu:", reply_markup=keyboard)
    else:
        await phone_menu(message)

@router.message(F.contact)
async def contact_handler(message: types.Message):
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
            phone=phone
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("❗ Siz allaqachon ro'yxatdan o'tgansiz.")
            await show_main_menu(message)
            return

    await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())
    await show_main_menu(message)



