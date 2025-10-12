from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.database import add_user

router = Router()

@router.message(CommandStart())
async def start_handler(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Botga xush kelibsiz! Iltimos, raqamingizni yuboring 👇", reply_markup=keyboard)


@router.message(F.contact)
async def contact_handler(message: types.Message):
    contact = message.contact
    username = message.from_user.username
    user_link = f"https://t.me/{username}" if username else None
    phone = contact.phone_number
    tg_id = message.from_user.id

    await add_user(tg_id, username, user_link, phone)

    main_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Harajatlar"), KeyboardButton(text="📝 Vazifalar")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz ✅\nEndi quyidagi bo‘limlardan birini tanlang 👇",
        reply_markup=main_keyboard
    )
