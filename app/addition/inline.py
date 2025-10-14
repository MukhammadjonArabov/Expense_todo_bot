from aiogram import Router, types, F
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


def get_pagination_keyboard(page: int, has_next: bool):
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Orqaga", callback_data=f"expenses_page:{page - 1}"
            )
        )
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Keyingilar", callback_data=f"expenses_page:{page + 1}"
            )
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[nav_buttons])
    return keyboard


def get_expenses_action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🗑 O'chirish"),
                KeyboardButton(text="🔙 Menyuga qaytish"),
            ]
        ],
        resize_keyboard=True
    )


def get_expense_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Harajat qo'shish")],
            [types.KeyboardButton(text="📋 Harajatlar ro'yxati")],
            [types.KeyboardButton(text="📊 Harajatlar statistika")],
            [types.KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )