from datetime import datetime, timezone
from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.alert import Alert
from app.services.alert_service import check_price_alert, check_volume_alert


async def check_active_alerts():
    """Evaluate all active alerts against current market data."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Alert).where(Alert.is_active == True))
            alerts = result.scalars().all()

            for alert in alerts:
                triggered = False
                if alert.alert_type in ("price_above", "price_below"):
                    triggered = await check_price_alert(alert.symbol, alert.condition)
                elif alert.alert_type == "volume_surge":
                    triggered = await check_volume_alert(alert.symbol, alert.condition)

                alert.last_checked_at = datetime.now(timezone.utc)
                if triggered:
                    alert.triggered_at = datetime.now(timezone.utc)
                    print(f"Alert triggered: {alert.symbol} - {alert.alert_type}")

            await db.commit()
        except Exception:
            await db.rollback()
