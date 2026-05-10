from datetime import datetime, timezone
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.alert import Alert
from app.services.alert_service import (
    check_price_alert,
    check_daily_pct_alert,
    check_volume_alert,
    check_rsi_alert,
)


ALERT_DISPATCH = {
    "price_above": check_price_alert,
    "price_below": check_price_alert,
    "daily_pct_change": check_daily_pct_alert,
    "volume_surge": check_volume_alert,
    "rsi_above": check_rsi_alert,
    "rsi_below": check_rsi_alert,
}


async def check_active_alerts():
    """Evaluate all active alerts against current market data."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Alert).where(Alert.is_active == True))
            alerts = result.scalars().all()

            for alert in alerts:
                checker = ALERT_DISPATCH.get(alert.alert_type)
                if checker is None:
                    continue

                triggered = await checker(alert.symbol, alert.condition)
                alert.last_checked_at = datetime.now(timezone.utc)
                if triggered:
                    alert.triggered_at = datetime.now(timezone.utc)

            await db.commit()
        except Exception:
            await db.rollback()
