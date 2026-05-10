from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services import chat_service, portfolio_service, macro_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    last_ticker: str = ""


class ChatResponse(BaseModel):
    response: str
    ticker_context: str = ""


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI Investing Assistant with follow-up context support."""
    context = {}
    try:
        portfolio_summary = await portfolio_service.get_portfolio_summary(db, current_user.id)
        context["portfolio"] = {
            "total_value": float(portfolio_summary.total_value),
            "total_cost": float(portfolio_summary.total_cost),
            "total_pnl_pct": portfolio_summary.total_pnl_pct,
            "holding_count": portfolio_summary.holding_count,
            "portfolio_count": portfolio_summary.portfolio_count,
        }
    except Exception:
        pass
    try:
        indices = await macro_service.get_indices(db)
        context["market"] = [
            {"symbol": i.symbol, "value": float(i.current_value) if i.current_value else None, "change_pct": float(i.daily_change_pct) if i.daily_change_pct else None}
            for i in indices[:5]
        ]
    except Exception:
        pass

    last = body.last_ticker.strip() or None
    response, ticker = await chat_service.get_chat_response(body.message, context, last)
    return ChatResponse(response=response, ticker_context=ticker or "")
