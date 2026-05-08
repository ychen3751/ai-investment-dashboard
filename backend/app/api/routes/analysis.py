from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analysis import ChatRequest
from app.services import analysis_service
from app.core.config import settings

router = APIRouter()


@router.get("/fundamental/{symbol}")
async def fundamental_analysis(symbol: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """AI-powered fundamental analysis. Falls back to rule-based if no OPENAI_API_KEY."""
    has_openai = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key")
    if has_openai:
        analysis = await analysis_service.get_fundamental_analysis(db, symbol)
    else:
        analysis = await analysis_service.get_rule_based_analysis(symbol)
    return {"symbol": symbol.upper(), "analysis": analysis}


@router.get("/fundamental-fallback/{symbol}")
async def fundamental_analysis_fallback(symbol: str, current_user: User = Depends(get_current_user)):
    """Rule-based analysis using yfinance data (no OpenAI key needed)."""
    analysis = await analysis_service.get_rule_based_analysis(symbol)
    return {"symbol": symbol.upper(), "analysis": analysis}


@router.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    response = await analysis_service.chat_message(db, current_user.id, request.symbol, request.message)
    history = await analysis_service.get_chat_history(db, current_user.id, request.symbol)
    return {"symbol": request.symbol.upper(), "response": response, "history": history}


@router.get("/history/{symbol}")
async def get_history(symbol: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    history = await analysis_service.get_chat_history(db, current_user.id, symbol)
    analyses = await analysis_service.get_analysis_history(db, symbol)
    return {
        "symbol": symbol.upper(),
        "chat_history": history,
        "analyses": [{"type": a.analysis_type, "content": a.content, "created_at": a.created_at} for a in analyses],
    }
