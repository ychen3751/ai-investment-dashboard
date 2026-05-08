from app.db.session import async_session_factory
from app.services import earnings_service


async def update_earnings_calendar():
    """Refresh earnings calendar data."""
    async with async_session_factory() as db:
        try:
            count = await earnings_service.update_calendar(db)
            if count > 0:
                print(f"Earnings updater: added {count} new events")
            await db.commit()
        except Exception:
            await db.rollback()
