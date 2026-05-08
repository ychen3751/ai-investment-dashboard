from app.db.session import async_session_factory
from app.services import options_service


async def scan_options_flow():
    """Scan options chains for unusual activity."""
    symbols_to_scan = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "GOOGL", "JPM"]
    async with async_session_factory() as db:
        try:
            count = await options_service.scan_unusual_activity(db, symbols_to_scan)
            if count > 0:
                print(f"Options scanner: found {count} unusual events")
            await db.commit()
        except Exception:
            await db.rollback()
