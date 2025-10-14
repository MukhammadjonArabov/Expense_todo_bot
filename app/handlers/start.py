from aiogram import Router, types, F
from aiogram.filters import Command
from app.database import async_session, User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

router = Router()


# /start komandasi
@router.message(Command("start"))
async def start_handler(message: types.Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    user_link = f"https://t.me/{username}" if username else None

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

    if user:
        await show_main_menu(message)
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "👋 Salom! Iltimos, ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            reply_markup=keyboard
        )

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


async def show_main_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="💰 Harajatlar"), types.KeyboardButton(text="📝 Vazifalar")]
        ],
        resize_keyboard=True
    )
    await message.answer("🏠 Asosiy menyu:", reply_markup=keyboard)
