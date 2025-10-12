from aiogram import Router, types
from aiogram.filters import Command
from app.database import async_session, User
from sqlalchemy import select

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    tg_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

    if user:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz! 😊")
    else:
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "Iltimos, telefon raqamingizni yuboring:",
            reply_markup=keyboard
        )