from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func, extract
from app.database import async_session, PersonalTask
from app.addition.functions import get_user, TZ
from datetime import datetime

TASKS_PER_PAGE = 10


# 🔹 Yillar ro‘yxatini olish
async def get_years_keyboard(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(func.extract('year', PersonalTask.deadline))
            .where(PersonalTask.user_id == user_id)
            .distinct()
            .order_by(func.extract('year', PersonalTask.deadline).desc())
        )
        years = [int(r[0]) for r in result.all()]

    if not years:
        return None

    keyboard = [
        [InlineKeyboardButton(text=f"📅 {year}", callback_data=f"tasks_year:{year}")]
        for year in years
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# 🔹 Oylik ro‘yxatni olish
async def get_months_keyboard(user_id: int, year: int):
    async with async_session() as session:
        result = await session.execute(
            select(func.extract('month', PersonalTask.deadline))
            .where(
                (PersonalTask.user_id == user_id) &
                (func.extract('year', PersonalTask.deadline) == year)
            )
            .distinct()
            .order_by(func.extract('month', PersonalTask.deadline))
        )
        months = [int(row[0]) for row in result.all()]

    if not months:
        return None

    month_names = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
        "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"
    ]

    keyboard = [
        [InlineKeyboardButton(
            text=f"📆 {month_names[m - 1]}",
            callback_data=f"tasks_month:{year}:{m}"
        )]
        for m in months
    ]
    keyboard.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_task_years")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# 🔹 Oy tanlanganda — Rejalar, Bajarilgan, Bajarilmagan bo‘limlari
def get_task_type_keyboard(year: int, month: int):
    keyboard = [
        [
            InlineKeyboardButton(text="🗓 Rejalar", callback_data=f"tasks_type:future:{year}:{month}:1"),
        ],
        [
            InlineKeyboardButton(text="✅ Bajarilgan", callback_data=f"tasks_type:done:{year}:{month}:1"),
            InlineKeyboardButton(text="❌ Bajarilmagan", callback_data=f"tasks_type:undone:{year}:{month}:1"),
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"tasks_year:{year}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# 🔹 Tanlangan turdagi vazifalarni olish (rejalar / bajarilgan / bajarilmagan)
async def get_tasks_list(user_id: int, year: int, month: int, t_type: str, page: int):
    now = datetime.now(TZ).date()
    offset = (page - 1) * TASKS_PER_PAGE

    async with async_session() as session:
        query = select(PersonalTask).where(
            (PersonalTask.user_id == user_id) &
            (extract('year', PersonalTask.deadline) == year) &
            (extract('month', PersonalTask.deadline) == month)
        )

        if t_type == "future":
            query = query.where(PersonalTask.deadline >= now)
        elif t_type == "done":
            query = query.where(PersonalTask.is_completed == 1, PersonalTask.deadline <= now)
        elif t_type == "undone":
            query = query.where(PersonalTask.is_completed == 0, PersonalTask.deadline <= now)

        query = query.order_by(PersonalTask.deadline.asc()).offset(offset).limit(TASKS_PER_PAGE)
        result = await session.execute(query)
        tasks = result.scalars().all()

        # Umumiy son
        count_query = select(func.count()).select_from(
            PersonalTask
        ).where(
            (PersonalTask.user_id == user_id) &
            (extract('year', PersonalTask.deadline) == year) &
            (extract('month', PersonalTask.deadline) == month)
        )
        if t_type == "future":
            count_query = count_query.where(PersonalTask.deadline >= now)
        elif t_type == "done":
            count_query = count_query.where(PersonalTask.is_completed == 1, PersonalTask.deadline <= now)
        elif t_type == "undone":
            count_query = count_query.where(PersonalTask.is_completed == 0, PersonalTask.deadline <= now)

        total_count = (await session.execute(count_query)).scalar()

    total_pages = (total_count + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    return tasks, total_pages


# 🔹 Sahifa navigatsiyasi uchun inline keyboard
def get_pagination_keyboard(year: int, month: int, t_type: str, page: int, total_pages: int):
    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"tasks_type:{t_type}:{year}:{month}:{page-1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("➡️ Keyingisi", callback_data=f"tasks_type:{t_type}:{year}:{month}:{page+1}"))

    navigation = [buttons] if buttons else []
    navigation.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"tasks_month:{year}:{month}")])
    return InlineKeyboardMarkup(inline_keyboard=navigation)
