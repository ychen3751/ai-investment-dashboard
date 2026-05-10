"""Market news intelligence — fetches, analyzes, and summarizes financial news.

Fetches headlines for major market drivers, performs rule-based sentiment
analysis, and organizes by sector/ticker impact.  Optional OpenAI for
professional narrative summarization.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.external import yahoo_finance
from app.services import market_data_service

# Major market symbols to track for news
TRACKED_SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "V", "WMT"]

BULLISH_KEYWORDS = [
    "surge", "rally", "bullish", "beat", "upgrade", "outperform", "growth", "positive",
    "gains", "higher", "raised", "exceed", "strong", "momentum", "breakout", "record",
    "expansion", "innovation", "partnership", "approval", "bull run",
]

BEARISH_KEYWORDS = [
    "plunge", "crash", "bearish", "downgrade", "miss", "cut", "decline", "negative",
    "losses", "lower", "downgrade", "weak", "selloff", "volatile", "fear", "panic",
    "recession", "inflation", "rate hike", "tariff", "sanctions", "uncertainty",
]


async def get_market_news_summary() -> Dict[str, Any]:
    """Full market news intelligence summary."""
    all_headlines: List[Dict[str, Any]] = []
    sector_mentions: Dict[str, List[str]] = {s: [] for s in ["Technology", "Finance", "Energy", "Healthcare", "Consumer", "Macro"]}
    ticker_sentiment: Dict[str, List[float]] = {}

    for symbol in TRACKED_SYMBOLS:
        try:
            info = await yahoo_finance.get_info(symbol)
            if not info:
                continue
            news_items = info.get("news", []) if isinstance(info.get("news"), list) else []
            for item in news_items[:5]:
                if not isinstance(item, dict):
                    continue
                title = item.get("title", "")
                if not title:
                    continue

                sentiment_score = _analyze_sentiment(title)
                sector = _categorize_sector(symbol, title)

                headline = {
                    "title": title,
                    "symbol": symbol,
                    "publisher": item.get("publisher", ""),
                    "published": datetime.fromtimestamp(item["providerPublishTime"]).isoformat()
                    if item.get("providerPublishTime") else None,
                    "link": item.get("link", ""),
                    "sentiment": sentiment_score["label"],
                    "score": sentiment_score["score"],
                    "sector": sector,
                }
                all_headlines.append(headline)

                if sector in sector_mentions:
                    sector_mentions[sector].append(title)
                if symbol not in ticker_sentiment:
                    ticker_sentiment[symbol] = []
                ticker_sentiment[symbol].append(sentiment_score["score"])

        except Exception:
            continue

    # Sort by sentiment strength (most extreme first)
    all_headlines.sort(key=lambda x: abs(x["score"] - 0.5), reverse=True)

    # ── Overall sentiment ──────────────────────────────────────────────
    avg_scores = []
    for sym, scores in ticker_sentiment.items():
        if scores:
            avg_scores.append((sym, sum(scores) / len(scores)))

    overall = sum(s[1] for s in avg_scores) / len(avg_scores) if avg_scores else 0.5
    overall_label = _sentiment_label(overall)
    confidence = int(abs(overall - 0.5) * 200)

    # ── Top headlines (most impactful) ─────────────────────────────────
    top_headlines = all_headlines[:8]

    # ── Sector impacts ─────────────────────────────────────────────────
    sector_impacts = []
    for sector, articles in sector_mentions.items():
        if articles:
            sent_scores = [a["score"] for a in all_headlines if a.get("sector") == sector]
            avg_sec = sum(sent_scores) / len(sent_scores) if sent_scores else 0.5
            sector_impacts.append({
                "sector": sector,
                "sentiment": _sentiment_label(avg_sec),
                "confidence": int(abs(avg_sec - 0.5) * 200),
                "headline_count": len(articles),
            })
    sector_impacts.sort(key=lambda x: x["headline_count"], reverse=True)

    # ── Ticker impacts ─────────────────────────────────────────────────
    ticker_impacts = []
    for sym, scores in sorted(ticker_sentiment.items(), key=lambda x: len(x[1]), reverse=True):
        if scores:
            avg_t = sum(scores) / len(scores)
            ticker_impacts.append({
                "symbol": sym,
                "sentiment": _sentiment_label(avg_t),
                "confidence": int(abs(avg_t - 0.5) * 200),
                "headline_count": len(scores),
            })

    # ── Macro themes ───────────────────────────────────────────────────
    macro_themes = _extract_macro_themes(all_headlines)

    # ── Market summary ─────────────────────────────────────────────────
    summary = _generate_summary(overall_label, overall, sector_impacts, ticker_impacts, top_headlines)

    # ── Optional OpenAI ────────────────────────────────────────────────
    ai_summary = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            headlines_text = "; ".join(h["title"][:80] for h in top_headlines[:5])
            prompt = (
                f"Market news sentiment: {overall_label} ({confidence}% confidence). "
                f"Headlines: {headlines_text}. "
                f"Write 2-3 sentences summarizing market sentiment. Do NOT give financial advice."
            )
            from app.external.openai_client import chat_query as openai_chat
            result = await openai_chat("MARKET", prompt, [])
            if result and "not configured" not in result:
                ai_summary = result
        except Exception:
            pass

    return {
        "overall_sentiment": overall_label,
        "confidence": confidence,
        "market_summary": ai_summary or summary,
        "top_headlines": top_headlines,
        "sector_impacts": sector_impacts,
        "macro_themes": macro_themes,
        "ticker_impacts": ticker_impacts,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _analyze_sentiment(text: str) -> Dict[str, Any]:
    """Rule-based sentiment analysis using keyword matching."""
    text_lower = text.lower()
    bullish_score = sum(2 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_score = sum(2 for kw in BEARISH_KEYWORDS if kw in text_lower)
    total = bullish_score + bearish_score
    if total == 0:
        return {"label": "neutral", "score": 0.5}
    normalized = bullish_score / total
    return {"label": _sentiment_label(normalized), "score": normalized}


def _sentiment_label(score: float) -> str:
    if score > 0.6:
        return "bullish"
    if score < 0.4:
        return "bearish"
    return "neutral"


def _categorize_sector(symbol: str, title: str) -> str:
    tech = ["AAPL", "MSFT", "GOOGL", "NVDA", "QQQ", "META"]
    finance = ["JPM", "V"]
    energy = ["XLE"]
    consumer = ["AMZN", "WMT"]
    if symbol in tech:
        return "Technology"
    if symbol in finance:
        return "Finance"
    if symbol in consumer:
        return "Consumer"
    title_lower = title.lower()
    if any(w in title_lower for w in ["federal reserve", "fed", "cpi", "inflation", "gdp", "treasury", "yield"]):
        return "Macro"
    if any(w in title_lower for w in ["energy", "oil", "gas"]):
        return "Energy"
    if any(w in title_lower for w in ["health", "drug", "fda"]):
        return "Healthcare"
    if any(w in title_lower for w in ["tech", "ai", "semiconductor", "software"]):
        return "Technology"
    return "Macro"


def _extract_macro_themes(headlines: List[Dict]) -> List[Dict]:
    themes = []
    theme_keywords = [
        ("Inflation & Fed Policy", ["inflation", "fed", "federal reserve", "rate hike", "cpi", "ppI"]),
        ("AI & Technology", ["ai", "artificial intelligence", "semiconductor", "nvidia", "chatgpt"]),
        ("Earnings Season", ["earnings", "quarterly", "revenue", "profit"]),
        ("Geopolitics", ["tariff", "sanctions", "trade", "china", "war", "defense"]),
        ("Energy & Commodities", ["oil", "energy", "gas", "commodity"]),
        ("M&A / Corporate", ["acquisition", "merger", "ipo", "buyout"]),
    ]
    for theme_name, keywords in theme_keywords:
        matching = [h for h in headlines if any(kw in (h.get("title", "") or "").lower() for kw in keywords)]
        if matching:
            sentiments = [h["score"] for h in matching]
            avg_s = sum(sentiments) / len(sentiments) if sentiments else 0.5
            themes.append({
                "theme": theme_name,
                "sentiment": _sentiment_label(avg_s),
                "headline_count": len(matching),
            })
    themes.sort(key=lambda x: x["headline_count"], reverse=True)
    return themes


def _generate_summary(sentiment: str, score: float, sectors: List[Dict], tickers: List[Dict], headlines: List[Dict]) -> str:
    parts = [f"Market sentiment is {sentiment} with {int(abs(score - 0.5) * 200)}% confidence."]
    if sectors:
        top = sectors[0]
        parts.append(f"Leading sector: {top['sector']} ({top['sentiment']}).")
    if tickers:
        parts.append(f"Key tickers: {', '.join(t['symbol'] for t in tickers[:3])}.")
    if headlines:
        parts.append(f"Top story: {headlines[0]['title'][:100]}.")
    return " ".join(parts)
