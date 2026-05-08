from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings

scheduler = AsyncIOScheduler()


def start_scheduler():
    if scheduler.running:
        return

    from app.tasks.price_poller import poll_prices
    from app.tasks.options_scanner import scan_options_flow
    from app.tasks.macro_updater import update_macro_data
    from app.tasks.earnings_updater import update_earnings_calendar
    from app.tasks.alert_checker import check_active_alerts

    scheduler.add_job(
        poll_prices,
        "interval",
        seconds=30,
        id="price_poller",
        replace_existing=True,
        misfire_grace_time=10,
    )
    scheduler.add_job(
        scan_options_flow,
        "interval",
        minutes=5,
        id="options_scanner",
        replace_existing=True,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        update_macro_data,
        "interval",
        seconds=60,
        id="macro_updater",
        replace_existing=True,
        misfire_grace_time=30,
    )
    scheduler.add_job(
        update_earnings_calendar,
        "interval",
        hours=6,
        id="earnings_updater",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        check_active_alerts,
        "interval",
        seconds=60,
        id="alert_checker",
        replace_existing=True,
        misfire_grace_time=30,
    )

    if settings.DEBUG:
        print("Scheduler started with all background jobs.")
