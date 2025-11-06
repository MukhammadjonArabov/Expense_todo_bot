from datetime import datetime
from aiogram import Bot
from sqlalchemy import select, and_, extract, func
from app.database import async_session, User, PersonalTask, Expense
import pytz

TZ = pytz.timezone("Asia/Tashkent")


async def send_morning_notifications(bot: Bot):
    """06:00 dagi ertalabki xabarlar"""
    now = datetime.now(TZ)
    today = now.date()

    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()

        for user in users:
            tasks = (
                await session.execute(
                    select(PersonalTask).where(
                        and_(PersonalTask.user_id == user.id, PersonalTask.deadline == today)
                    )
                )
            ).scalars().all()

            if tasks:
                text = (
                    f"🌅 *Assalomu alaykum, {user.username or 'do‘stim'}!* ☀️\n\n"
                    f"Bugungi rejalaringiz:\n"
                )
                for t in tasks:
                    text += f"- {t.title}\n"
                text += "\n🔥 Omad sizga yor bo‘lsin!"
            else:
                text = (
                    f"🌞 *Xayrli tong, {user.username or 'do‘stim'}!* ☕\n\n"
                    f"Bugun uchun hali maqsad qo‘ymadingiz 😴\n"
                    f"Yangi kun — yangi imkoniyatlar 💪"
                )

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="Markdown")
            except Exception as e:
                print(f"❌ Xabar yuborilmadi ({user.telegram_id}): {e}")


async def send_evening_notifications(bot: Bot):
    """20:00 dagi kechqurungi xabarlar"""
    now = datetime.now(TZ)
    today = now.date()

    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()

        for user in users:
            tasks = (
                await session.execute(
                    select(PersonalTask).where(
                        and_(PersonalTask.user_id == user.id, PersonalTask.deadline == today)
                    )
                )
            ).scalars().all()

            if not tasks:
                text = (
                    f"🌇 *Salom, {user.username or 'do‘stim'}!* 🌙\n\n"
                    f"Bugun uchun maqsad qo‘ymagandingiz 😅\n"
                    f"Ertangi kunni kuchli boshlash uchun hoziroq rejalashtiring! 💡"
                )
            else:
                done = [t for t in tasks if t.is_completed]
                undone = [t for t in tasks if not t.is_completed]

                text = f"🌙 *Kun yakuni* 📅\n\n"
                if done:
                    text += "✅ *Bajarilganlar:*\n"
                    for t in done:
                        text += f" • {t.title}\n"
                    text += "\n"
                if undone:
                    text += "❌ *Bajarilmaganlar:*\n"
                    for t in undone:
                        text += f" • {t.title}\n"
                    text += "\n"

                text += (
                    "💭 Har kuni kichik qadamlar bilan katta natijalarga erishasiz 💪\n"
                    "Ertangi kunga yangi maqsadlar qo‘ying 🚀"
                )

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="Markdown")
            except Exception as e:
                print(f"❌ Kechqurun xabar yuborilmadi ({user.telegram_id}): {e}")


async def send_midday_notifications(bot: Bot):
    now = datetime.now(TZ)
    today = now.date()

    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()

        for user in users:
            tasks = (
                await session.execute(
                    select(PersonalTask).where(
                        and_(PersonalTask.user_id == user.id, PersonalTask.deadline == today)
                    )
                )
            ).scalars().all()

            if not tasks:
                text = (
                    f"🕛 *Salom, {user.username or 'do‘stim'}!* 😇\n\n"
                    f"Bugun hali hech qanday maqsad belgilanmadi.\n"
                    f"Tushlikdan keyin ham kech emas — bugun nimalarga erishmoqchisiz? ✍️"
                )
            else:
                done = [t for t in tasks if t.is_completed == 1]
                undone = [t for t in tasks if t.is_completed == 0]

                text = f"⏰ *Bugungi eslatma* 🗓\n\n"
                if undone:
                    text += "⚡️ *Hali bajarilmagan vazifalar:*\n"
                    for t in undone:
                        text += f" • {t.title}\n"
                    text += "\n"
                if done:
                    text += "✅ *Allaqachon bajarilganlar:*\n"
                    for t in done:
                        text += f" • {t.title}\n"
                    text += "\n"

                text += "🚀 Tushlikdan keyin ham samarali bo‘lishni unutmang!"

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="Markdown")
            except Exception as e:
                print(f"❌ Tushlikdagi eslatma yuborilmadi ({user.telegram_id}): {e}")

async def send_expense_summary(bot: Bot):
    now = datetime.now(TZ)
    today = now.date()
    current_month = now.month
    current_year = now.year

    async with async_session() as session:
        users = (await session.execute(select(User))).scalars().all()

        for user in users:
            # 🔹 Bugungi xarajatlar
            today_expenses = (
                await session.execute(
                    select(func.sum(Expense.amount))
                    .where(
                        and_(
                            Expense.user_id == user.id,
                            func.date(Expense.created_at) == today,
                        )
                    )
                )
            ).scalar() or 0

            # 🔹 Shu oydagi jami xarajatlar
            month_expenses = (
                await session.execute(
                    select(func.sum(Expense.amount))
                    .where(
                        and_(
                            Expense.user_id == user.id,
                            extract("month", Expense.created_at) == current_month,
                            extract("year", Expense.created_at) == current_year,
                        )
                    )
                )
            ).scalar() or 0

            # 🔹 Xabar matni
            if today_expenses == 0:
                text = (
                    f"💰 *Salom, {user.username or 'do‘stim'}!* 📊\n\n"
                    f"Bugun hali xarajat qo‘shmagansiz 😴\n"
                    f"Har bir so‘mni nazorat qilish — muvaffaqiyat kaliti 💡\n\n"
                    f"📆 Joriy oydagi umumiy xarajatlaringiz: *{month_expenses:,} so‘m*"
                )
            else:
                text = (
                    f"💸 *Kun yakuni: Harajatlar hisobi* 🕢\n\n"
                    f"📅 Bugungi xarajatlaringiz: *{today_expenses:,} so‘m*\n"
                    f"📆 Joriy oydagi jami xarajatlar: *{month_expenses:,} so‘m*\n\n"
                    f"💭 Moliyani nazorat qilish — barqarorlik garovi 💪"
                )

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="Markdown")
            except Exception as e:
                print(f"❌ Harajat xabari yuborilmadi ({user.telegram_id}): {e}")