from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.addition.functions import TZ
from app.services.notifications import (
    send_morning_notifications,
    send_evening_notifications, send_midday_notifications, send_expense_summary,
)

def setup_scheduler(bot):
    """Har kuni 06:00, 12:00 va 20:00 da xabar yuborish uchun scheduler"""

    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(
        send_morning_notifications,
        trigger=CronTrigger(hour=6, minute=0, timezone=TZ),
        args=[bot],
        id="morning_job",
        replace_existing=True,
    )

    scheduler.add_job(
        send_evening_notifications,
        trigger=CronTrigger(hour=20, minute=0, timezone=TZ),
        args=[bot],
        id="evening_job",
        replace_existing=True,
    )

    scheduler.add_job(
        send_midday_notifications,
        trigger=CronTrigger(hour=12, minute=0, timezone=TZ),
        args=[bot],
        id="midday_job",
        replace_existing=True,
    )

    scheduler.add_job(
        send_expense_summary,
        trigger=CronTrigger(hour=20, minute=30, timezone=TZ),
        args=[bot],
        id="expense_summary_job",
        replace_existing=True,
    )

    scheduler.start()

    return scheduler
