from fastapi import APIRouter

from app.api.routes import auth, portfolios, market, technical, analysis, options, earnings, watchlists, alerts, macro, risk, news, chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(technical.router, prefix="/technical", tags=["technical"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(options.router, prefix="/options", tags=["options"])
api_router.include_router(earnings.router, prefix="/earnings", tags=["earnings"])
api_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(macro.router, prefix="/macro", tags=["macro"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import portfolio_service, macro_service


@api_router.get("/dashboard/summary", tags=["dashboard"])
async def get_dashboard_summary(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio_summary = await portfolio_service.get_portfolio_summary(db, current_user.id)
    indices = await macro_service.get_indices(db)
    return {
        "portfolio": {
            "total_value": float(portfolio_summary.total_value),
            "total_cost": float(portfolio_summary.total_cost),
            "total_pnl": float(portfolio_summary.total_pnl),
            "total_pnl_pct": portfolio_summary.total_pnl_pct,
            "day_pnl": float(portfolio_summary.day_pnl),
            "portfolio_count": portfolio_summary.portfolio_count,
            "holding_count": portfolio_summary.holding_count,
        },
        "market": [
            {
                "symbol": i.symbol,
                "name": i.name,
                "value": float(i.current_value) if i.current_value else None,
                "change": float(i.daily_change) if i.daily_change else None,
                "change_pct": float(i.daily_change_pct) if i.daily_change_pct else None,
            }
            for i in indices
        ],
    }
