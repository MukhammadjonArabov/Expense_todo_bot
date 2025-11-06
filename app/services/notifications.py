from datetime import datetime
from aiogram import Bot
from sqlalchemy import select, and_
from app.database import async_session, User, PersonalTask
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