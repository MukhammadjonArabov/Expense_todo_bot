from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.notifications import (
    send_morning_notifications,
    send_evening_notifications,
)
import pytz

TZ = pytz.timezone("Asia/Tashkent")


def setup_scheduler(bot):
    """Har kuni 06:00 va 20:00 da xabar yuborish uchun scheduler"""

    scheduler = AsyncIOScheduler(timezone=TZ)

    # 06:00 — ertalabki xabar
    scheduler.add_job(
        send_morning_notifications,
        trigger=CronTrigger(hour=6, minute=0, timezone=TZ),
        args=[bot],
        id="morning_job",
        replace_existing=True,
    )

    # 20:00 — kechqurungi xabar
    scheduler.add_job(
        send_evening_notifications,
        trigger=CronTrigger(hour=20, minute=0, timezone=TZ),
        args=[bot],
        id="evening_job",
        replace_existing=True,
    )

    scheduler.start()
    print("⏰ Scheduler ishga tushdi (06:00 va 20:00 uchun)")

    return scheduler
