from fastapi import APIRouter

from app.services import news_intelligence_service

router = APIRouter()


@router.get("/market-summary")
async def get_market_news_summary():
    """AI market news intelligence: sentiment, headlines, sector/ticker impacts.

    Fetches real news from Yahoo Finance, performs rule-based sentiment analysis,
    and organizes headlines by sector, ticker, and macro theme.
    Educational purposes only — not financial advice.
    """
    return await news_intelligence_service.get_market_news_summary()
