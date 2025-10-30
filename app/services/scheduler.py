import aiocron
from app.services.notifications import (
    send_morning_notifications,
    send_evening_notifications,
)

async def setup_scheduler(bot):
    """Har kuni belgilangan vaqtda xabar yuborishni yo‘lga qo‘yadi"""

    @aiocron.crontab("0 6 * * *", tz="Asia/Tashkent")  # har kuni 06:00 da
    async def morning():
        await send_morning_notifications(bot)

    @aiocron.crontab("0 20 * * *", tz="Asia/Tashkent")  # har kuni 20:00 da
    async def evening():
        await send_evening_notifications(bot)
