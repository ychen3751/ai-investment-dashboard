import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.external import openai_client, yahoo_finance
from app.models.stock_analysis import StockAnalysis
from app.models.chat_message import ChatMessage
from app.core.cache import get_redis


async def get_fundamental_analysis(db: AsyncSession, symbol: str) -> Dict[str, Any]:
    redis = await get_redis()
    cache_key = f"analysis:{symbol.upper()}:fundamental"
    cached = await redis.get(cache_key)
    if cached:
        import json
        return json.loads(cached)

    result = await db.execute(
        select(StockAnalysis).where(
            StockAnalysis.symbol == symbol.upper(),
            StockAnalysis.analysis_type == "fundamental",
        ).order_by(StockAnalysis.created_at.desc()).limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        import json
        await redis.setex(cache_key, 3600, json.dumps(existing.content, default=str))
        return existing.content

    info = await yahoo_finance.get_info(symbol)
    company_name = info.get("shortName") or info.get("longName") or symbol

    financial_data = {
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "profit_margins": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "revenue": info.get("totalRevenue"),
        "debt_to_equity": info.get("debtToEquity"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }

    analysis = await openai_client.analyze_fundamental(symbol, company_name, financial_data)

    record = StockAnalysis(
        symbol=symbol.upper(),
        analysis_type="fundamental",
        content=analysis,
        model_used="gpt-4o-mini",
    )
    db.add(record)
    await db.flush()

    import json
    await redis.setex(cache_key, 86400, json.dumps(analysis, default=str))
    return analysis


async def get_rule_based_analysis(symbol: str) -> Dict[str, Any]:
    """Fallback analysis using yfinance data and rule-based logic when no OpenAI key."""
    info = await yahoo_finance.get_info(symbol)
    history = await yahoo_finance.get_history(symbol, "1d", "1y")

    company_name = info.get("shortName") or info.get("longName") or symbol
    sector = info.get("sector") or "N/A"
    industry = info.get("industry") or "N/A"

    # Valuation analysis
    pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    pb = info.get("priceToBook")
    ps = info.get("priceToSalesTrailing12Months")

    valuation_score = 50
    valuation_factors = []
    if pe is not None:
        if pe < 15:
            valuation_score += 20
            valuation_factors.append(f"P/E of {pe:.1f} is below the market average, suggesting undervaluation")
        elif pe > 30:
            valuation_score -= 10
            valuation_factors.append(f"P/E of {pe:.1f} is elevated, suggesting premium pricing")
        else:
            valuation_factors.append(f"P/E of {pe:.1f} is in a reasonable range")

    # Trend analysis
    trend_score = 50
    trend_factors = []
    closes = [p["close"] for p in history] if history else []
    if len(closes) > 20:
        sma20 = sum(closes[-20:]) / 20
        sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        current = closes[-1]

        if current > sma20:
            trend_score += 15
            trend_factors.append("Price is above the 20-day moving average (short-term uptrend)")
        else:
            trend_score -= 10
            trend_factors.append("Price is below the 20-day moving average (short-term downtrend)")

        if sma50 and current > sma50:
            trend_score += 10
            trend_factors.append("Price is above the 50-day moving average (medium-term uptrend)")
        elif sma50:
            trend_score -= 10
            trend_factors.append("Price is below the 50-day moving average (medium-term downtrend)")

        # Check SMA 20/50 crossover
        if sma50 and len(closes) >= 50:
            if sma20 > sma50:
                trend_factors.append("Golden cross formation (20-day above 50-day MA) — bullish signal")
            else:
                trend_factors.append("Death cross formation (20-day below 50-day MA) — bearish signal")

        # RSI
        gains = []
        losses = []
        for i in range(1, min(15, len(closes))):
            diff = closes[-i] - closes[-i - 1]
            if diff >= 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        avg_gain = sum(gains) / max(len(gains), 1) if gains else 0
        avg_loss = sum(losses) / max(len(losses), 1) if losses else 0
        rsi = 50
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        if rsi > 70:
            trend_score -= 10
            trend_factors.append(f"RSI of {rsi:.0f} is in overbought territory")
        elif rsi < 30:
            trend_score += 10
            trend_factors.append(f"RSI of {rsi:.0f} is in oversold territory")
        else:
            trend_factors.append(f"RSI of {rsi:.0f} is neutral")

    # Risk analysis
    risk_score = 50
    risk_factors = []
    beta = info.get("beta")
    debt_equity = info.get("debtToEquity")

    if beta is not None:
        if beta < 0.8:
            risk_score += 10
            risk_factors.append(f"Low volatility (Beta={beta:.2f})")
        elif beta > 1.5:
            risk_score -= 15
            risk_factors.append(f"High volatility (Beta={beta:.2f})")
        else:
            risk_factors.append(f"Moderate volatility (Beta={beta:.2f})")

    if debt_equity is not None:
        if debt_equity > 100:
            risk_score -= 10
            risk_factors.append(f"Elevated debt-to-equity ratio ({debt_equity:.0f}%)")
        else:
            risk_score += 5
            risk_factors.append(f"Manageable debt-to-equity ratio ({debt_equity:.0f}%)")

    # Final verdict
    total_score = (valuation_score * 0.3 + trend_score * 0.4 + risk_score * 0.3)
    if total_score >= 65:
        verdict = "bullish"
    elif total_score >= 40:
        verdict = "neutral"
    else:
        verdict = "bearish"

    return {
        "company_summary": f"{company_name} ({symbol.upper()}) operates in the {sector} sector ({industry}). "
                          f"Market capitalization is ${(info.get('marketCap') or 0) / 1e9:.2f}B.",
        "valuation": {
            "score": valuation_score,
            "factors": valuation_factors,
        },
        "trend": {
            "score": trend_score,
            "factors": trend_factors,
        },
        "risk": {
            "score": risk_score,
            "factors": risk_factors,
        },
        "overall_assessment": verdict,
        "confidence_score": min(100, max(0, int(total_score))),
        "key_metrics": {
            "pe_ratio": pe,
            "forward_pe": forward_pe,
            "price_to_book": pb,
            "price_to_sales": ps,
            "beta": beta,
            "market_cap": info.get("marketCap"),
            "dividend_yield": info.get("dividendYield"),
            "revenue": info.get("totalRevenue"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
        },
        "source": "rule-based (yfinance)",
    }


async def chat_message(db: AsyncSession, user_id: uuid.UUID, symbol: str, message: str) -> str:
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.symbol == symbol.upper(),
        ).order_by(ChatMessage.created_at.desc()).limit(20)
    )
    history = result.scalars().all()

    chat_history = [{"role": "user" if m.role == "user" else "assistant", "content": m.content} for m in reversed(history)]
    response = await openai_client.chat_query(symbol, message, chat_history)

    db.add(ChatMessage(user_id=user_id, symbol=symbol.upper(), role="user", content=message))
    db.add(ChatMessage(user_id=user_id, symbol=symbol.upper(), role="assistant", content=response))
    await db.flush()

    return response


async def get_analysis_history(db: AsyncSession, symbol: str) -> List[StockAnalysis]:
    result = await db.execute(
        select(StockAnalysis).where(StockAnalysis.symbol == symbol.upper()).order_by(StockAnalysis.created_at.desc()).limit(10)
    )
    return result.scalars().all()


async def get_chat_history(db: AsyncSession, user_id: uuid.UUID, symbol: str) -> List[Dict]:
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.user_id == user_id,
            ChatMessage.symbol == symbol.upper(),
        ).order_by(ChatMessage.created_at.asc())
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in result.scalars().all()]
