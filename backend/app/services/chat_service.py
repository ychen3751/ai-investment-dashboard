"""AI Investing Assistant — classifies intent, extracts tickers, and returns
structured market analysis with real backend data where available.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

# ── Company alias → ticker map ───────────────────────────────────────────
COMPANY_ALIASES = {
    "intel": "INTC", "apple": "AAPL", "nvidia": "NVDA", "tesla": "TSLA",
    "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL", "amazon": "AMZN",
    "meta": "META", "facebook": "META", "amd": "AMD", "netflix": "NFLX",
    "disney": "DIS", "uber": "UBER", "palantir": "PLTR", "crowdstrike": "CRWD",
    "salesforce": "CRM", "adobe": "ADBE", "oracle": "ORCL", "cisco": "CSCO",
    "ibm": "IBM", "shopify": "SHOP", "sq": "SQ", "block": "SQ",
    "paypal": "PYPL", "intuit": "INTU", "snowflake": "SNOW", "datadog": "DDOG",
    "mongo": "MDB", "cloudflare": "NET", "coinbase": "COIN", "robinhood": "HOOD",
}


def extract_ticker(text: str) -> Optional[str]:
    """Extract ticker from user text — handles aliases and direct tickers."""
    text_lower = text.lower().strip()

    # Check aliases first
    for name, ticker in COMPANY_ALIASES.items():
        if name in text_lower:
            return ticker

    # Direct ticker pattern (2-5 uppercase letters, possibly with . or -)
    tokens = re.findall(r'\b[A-Z]{1,5}\b', text)
    known_tickers = {"AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMZN", "META",
                     "AMD", "INTC", "NFLX", "DIS", "UBER", "PLTR", "SPY", "QQQ",
                     "VIX", "DIA", "IWM", "CRWD", "SHOP", "SQ", "PYPL"}
    for t in tokens:
        if t in known_tickers:
            return t

    # If only one ticker-like word and it's isolated
    if len(tokens) == 1 and len(tokens[0]) >= 2:
        return tokens[0]

    return None


def classify_intent(text: str) -> str:
    """Classify user intent from message text."""
    t = text.lower().strip()

    # Follow-up: all / everything / more
    if t in ("all", "show all", "everything", "show everything", "tell me more", "more", "full analysis"):
        return "follow_up_all"

    # Options strategy
    if any(w in t for w in ["options strategy", "option strategy", "options trading", "option trade",
                              "covered call", "cash secured put", "spread", "iron condor",
                              "options for", "strategy for", "options recommendation"]):
        return "options_strategy"

    # Options flow
    if any(w in t for w in ["options flow", "option flow", "unusual options", "call put",
                              "put/call", "option chain", "flow analysis", "options activity"]):
        return "options_flow"

    # Technical analysis
    if any(w in t for w in ["technical", "rsi", "macd", "moving average", "sma", "ema",
                              "bollinger", "support", "resistance", "chart pattern",
                              "momentum indicator", "overbought", "oversold"]):
        return "technical_analysis"

    # Earnings
    if any(w in t for w in ["earnings", "quarterly", "eps", "revenue", "profit report",
                              "fiscal", "earnings date", "earnings report"]):
        return "earnings_analysis"

    # Portfolio
    if any(w in t for w in ["my portfolio", "portfolio risk", "portfolio analysis", "my holdings",
                              "my investments", "diversification", "how diversified",
                              "portfolio health", "my stocks", "my returns"]):
        return "portfolio_analysis"

    # Macro
    if any(w in t for w in ["vix", "market", "inflation", "cpi", "treasury", "yield",
                              "fed", "federal reserve", "interest rate", "recession",
                              "economy", "gdp", "bear market", "bull market",
                              "market sentiment", "risk on", "risk off"]):
        return "macro_question"

    # Ticker analysis (ticker mentioned + general analysis words)
    ticker = extract_ticker(text)
    if ticker:
        if any(w in t for w in ["rise", "fall", "buy", "sell", "bullish", "bearish",
                                  "outlook", "prospect", "forecast", "prediction",
                                  "target", "expect", "perform", "analyze",
                                  "think", "opinion", "recommend", "analysis",
                                  "about", "what about", "how about", "evaluate",
                                  "trend", "momentum", "strong", "weak"]):
            return "ticker_analysis"
        return "ticker_analysis"

    # Education
    if any(w in t for w in ["what is", "what does", "explain", "how does", "define",
                              "meaning", "understand", "beginner", "learn",
                              "tell me about", "what does it mean", "what are"]):
        return "education_question"

    return "unknown"


async def get_chat_response(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    last_ticker: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """Get response + ticker context for follow-ups."""
    intent = classify_intent(message)
    ticker = extract_ticker(message) or last_ticker

    # Follow-up: run full analysis on previous ticker
    if intent == "follow_up_all" and last_ticker:
        ticker = last_ticker
        return await _full_ticker_analysis(ticker), ticker

    if intent == "unknown" and last_ticker:
        ticker = last_ticker
        intent = "ticker_analysis"

    # Route to handler
    if intent == "ticker_analysis" and ticker:
        return await _ticker_analysis(ticker), ticker
    if intent == "options_strategy" and ticker:
        return await _options_strategy(ticker), ticker
    if intent == "options_flow" and ticker:
        return await _options_flow(ticker), ticker
    if intent == "technical_analysis" and ticker:
        return await _technical_analysis(ticker), ticker
    if intent == "earnings_analysis" and ticker:
        return await _earnings_analysis(ticker), ticker
    if intent == "portfolio_analysis":
        return _portfolio_analysis(context), None
    if intent == "macro_question" or "vix" in message.lower():
        return _macro_answer(message), None
    if intent == "education_question":
        return _education_answer(message), None

    return _fallback(), None


# ── Intent handlers ──────────────────────────────────────────────────────

async def _ticker_analysis(ticker: str) -> str:
    """Full ticker analysis with real backend data."""
    try:
        from app.services import market_data_service
        quote = await market_data_service.get_quote(ticker)
        price = float(quote["price"]) if quote and quote.get("price") else None
        change = float(quote["change_pct"]) if quote and quote.get("change_pct") else None
        name = quote.get("name", ticker) if quote else ticker
    except Exception:
        price, change, name = None, None, ticker

    # Technical data
    rsi_val, macd_sig, trend = None, None, None
    try:
        from app.services.technical_service import get_combined_analysis
        ta = await get_combined_analysis(ticker, "1d", "3mo")
        if ta and "rsi_14" in ta and ta["rsi_14"]:
            rsi_val = ta["rsi_14"][-1]
            if ta.get("signals"):
                signals = ta["signals"]
                for s in signals:
                    if "uptrend" in s.get("message","").lower() or "golden" in s.get("message","").lower():
                        trend = "uptrend"
                    elif "downtrend" in s.get("message","").lower() or "death" in s.get("message","").lower():
                        trend = "downtrend"
    except Exception:
        pass

    lines = [f"**{name} ({ticker}) Analysis**"]
    if price is not None:
        lines.append(f"Current price: **${price:.2f}** {f'({change:+.2f}%)' if change else ''}")
    if rsi_val is not None:
        rsi_line = f"RSI: **{rsi_val:.1f}**"
        if rsi_val > 70: rsi_line += " — overbought territory"
        elif rsi_val < 30: rsi_line += " — oversold territory"
        else: rsi_line += " — neutral range"
        lines.append(rsi_line)
    if trend:
        lines.append(f"Trend: **{trend}**")
    lines.append("")
    lines.append("**Bullish Factors**")
    lines.append(f"• {name} is a leading company in its sector with strong market position")
    if change and change > 0:
        lines.append(f"• Positive price momentum today ({change:+.2f}%)")
    lines.append("")
    lines.append("**Bearish Risks**")
    if rsi_val and rsi_val > 70:
        lines.append(f"• RSI at {rsi_val:.1f} suggests the stock may be overextended short-term")
    if trend == "downtrend":
        lines.append("• Price is in a downtrend — momentum favors sellers")
    lines.append("• Sector and macro risks apply as with any equity investment")
    lines.append("")
    lines.append("**What This Means**")
    lines.append(f"{name} is currently showing {'positive' if change and change > 0 else 'mixed'} price action. "
                 f"The stock{' may be overbought in the near term' if rsi_val and rsi_val > 70 else ' appears reasonably valued based on momentum'}. "
                 f"As with all individual stocks, this analysis is educational — not financial advice.")
    return "\n".join(lines)


async def _options_strategy(ticker: str) -> str:
    try:
        from app.services import market_data_service
        quote = await market_data_service.get_quote(ticker)
        price = float(quote["price"]) if quote and quote.get("price") else None
    except Exception:
        price = None

    lines = [f"**Options Strategies for {ticker}**"]
    if price:
        lines.append(f"Current price: **${price:.2f}**")
    lines.append("")
    lines.append("**Strategy Ideas (Educational)**")
    lines.append("**1. Covered Call** — If you own shares, sell OTM calls to generate income")
    lines.append("• Best for: Neutral to slightly bullish outlook")
    lines.append("• Risk: Limited upside if stock rallies past strike")
    lines.append("")
    lines.append("**2. Cash-Secured Put** — Sell put at a price you'd want to buy")
    lines.append("• Best for: Bullish outlook, willing to buy on dip")
    lines.append("• Risk: Assignment at strike if stock falls")
    lines.append("")
    lines.append("**3. Bull Call Spread** — Buy lower strike, sell higher strike call")
    lines.append("• Best for: Moderate upside expectation")
    lines.append("• Risk: Limited to net premium paid")
    lines.append("")
    lines.append("**4. Protective Put** — Buy put as insurance for existing shares")
    lines.append("• Best for: Hedging downside while keeping upside")
    lines.append("• Risk: Premium cost erodes returns")
    lines.append("")
    lines.append("**Key Risks**")
    lines.append("• Time decay (theta) accelerates near expiration")
    lines.append("• Implied volatility crush can hurt long options")
    lines.append("• Earnings events cause unpredictable IV swings")
    lines.append("")
    lines.append("⚠️ This is educational — options trading involves substantial risk.")
    return "\n".join(lines)


async def _options_flow(ticker: str) -> str:
    try:
        from app.services.options_analysis_service import get_flow_analysis
        analysis = await get_flow_analysis(ticker)
        if analysis.get("overall_signal"):
            sig = analysis["overall_signal"]
            conf = analysis["confidence"]
            lines = [f"**Options Flow Analysis — {ticker.upper()}**"]
            lines.append(f"Signal: **{sig.upper()}** (confidence: {conf}%)")
            if analysis.get("summary"):
                lines.append(analysis["summary"])
            lines.append("")
            m = analysis.get("key_metrics", {})
            if m:
                lines.append(f"Call/Put Volume Ratio: **{m.get('call_put_volume_ratio', 'N/A')}x**")
                lines.append(f"Call/Put Premium Ratio: **{m.get('call_put_premium_ratio', 'N/A')}x**")
                lines.append(f"Unusual Contracts: **{m.get('unusual_count', 0)}**")
                if m.get('avg_implied_volatility'):
                    lines.append(f"Avg IV: **{m['avg_implied_volatility']:.1f}%**")
            lines.append("")
            factors = analysis.get("bullish_factors", [])
            if factors:
                lines.append("**Bullish Flow Signals**")
                for f in factors[:2]: lines.append(f"• {f}")
            factors = analysis.get("bearish_factors", [])
            if factors:
                lines.append("**Bearish Flow Signals**")
                for f in factors[:2]: lines.append(f"• {f}")
            return "\n".join(lines)
    except Exception:
        pass

    return (f"**Options Flow — {ticker.upper()}**\n\n"
            f"Options chain data is currently loading. For detailed flow analysis, "
            f"visit the Options Flow Scanner page.\n\n"
            f"⚠️ Educational purposes only.")


async def _technical_analysis(ticker: str) -> str:
    try:
        from app.services.technical_service import get_combined_analysis
        ta = await get_combined_analysis(ticker, "1d", "3mo")
        if not ta or "rsi_14" not in ta:
            raise ValueError("No data")
        rsi_val = ta["rsi_14"][-1] if ta["rsi_14"] else None
        macd = ta.get("macd", {})
        macd_hist = macd.get("histogram", [])
        macd_sig = macd.get("signal", [])
        closes = ta.get("prices", [])
        last_price = closes[-1] if closes else None
        sma20 = ta.get("sma_20", [])
        sma50 = ta.get("sma_50", [])
        above_sma20 = last_price > sma20[-1] if sma20 and sma20[-1] and last_price else None
        above_sma50 = last_price > sma50[-1] if sma50 and sma50[-1] and last_price else None
        signals = ta.get("signals", [])
    except Exception:
        return (f"**Technical Analysis — {ticker.upper()}**\n\n"
                f"Technical data is currently loading. Visit the Technical Analysis page for interactive charts.")

    lines = [f"**Technical Analysis — {ticker.upper()}**"]
    if last_price: lines.append(f"Price: **${last_price:.2f}**")
    if rsi_val:
        rsi_str = f"RSI(14): **{rsi_val:.1f}**"
        if rsi_val > 70: rsi_str += " (overbought)"
        elif rsi_val < 30: rsi_str += " (oversold)"
        lines.append(rsi_str)
    if macd_hist and len(macd_hist) > 2:
        last_h = macd_hist[-1]
        prev_h = macd_hist[-2]
        if last_h and prev_h:
            macd_str = f"MACD Histogram: **{last_h:.4f}**"
            if last_h > prev_h: macd_str += " (improving)"
            elif last_h < prev_h: macd_str += " (weakening)"
            lines.append(macd_str)
    if above_sma20 is not None:
        lines.append(f"Price vs SMA20: **{'Above ✓' if above_sma20 else 'Below ✗'}**")
    if above_sma50 is not None:
        lines.append(f"Price vs SMA50: **{'Above ✓' if above_sma50 else 'Below ✗'}**")
    if signals:
        lines.append("")
        lines.append("**Signals**")
        for s in signals:
            emoji = "🟢" if s["signal"] == "bullish" else "🔴" if s["signal"] == "bearish" else "⚪"
            lines.append(f"{emoji} {s['message']}")
    return "\n".join(lines)


async def _earnings_analysis(ticker: str) -> str:
    try:
        from app.services.earnings_analysis_service import get_earnings_analysis
        ea = await get_earnings_analysis(ticker)
    except Exception:
        return (f"**Earnings Analysis — {ticker.upper()}**\n\n"
                f"Earnings data is currently loading. Visit the Earnings Calendar page for details.")

    sig = ea.get("overall_signal", "neutral")
    conf = ea.get("confidence", 0)
    lines = [f"**Earnings Analysis — {ticker.upper()}**"]
    lines.append(f"Setup: **{sig.upper()}** (confidence: {conf}%)")
    if ea.get("summary"):
        lines.append(ea["summary"])
    ks = ea.get("key_signals", {})
    if ks:
        lines.append("")
        for k, v in ks.items():
            if v != "N/A" and v != "Insufficient data":
                lines.append(f"• {k.replace('_', ' ').title()}: **{v}**")
    return "\n".join(lines)


def _portfolio_analysis(ctx: Optional[Dict]) -> str:
    if not ctx or not ctx.get("portfolio"):
        return ("**Portfolio Analysis**\n\n"
                "I don't have portfolio data loaded. Please check your portfolio on the "
                "Portfolios page, then ask again.\n\n"
                "You can ask me about:\n"
                "• **Diversification** — How balanced is your portfolio?\n"
                "• **Risk** — Volatility, beta, and drawdown\n"
                "• **Concentration** — Overweight positions\n"
                "• **Sector exposure** — Where are you invested?")
    p = ctx["portfolio"]
    lines = [f"**Portfolio Overview**"]
    lines.append(f"Holdings: **{p.get('holding_count', 0)}**")
    lines.append(f"Total Value: **${p.get('total_value', 0):,.2f}**")
    pnl = p.get("total_pnl_pct", 0)
    lines.append(f"Total Return: **{pnl:+.2f}%**")
    lines.append("")
    lines.append("**Key Questions to Consider**")
    lines.append("• How diversified is your portfolio across sectors?")
    lines.append("• What is your portfolio's beta and volatility?")
    lines.append("• Are any positions overweight (>20%)?")
    lines.append("• Do you have exposure to defensive sectors?")
    lines.append("")
    lines.append("For detailed risk analytics, visit the Risk Analytics page.")
    return "\n".join(lines)


def _macro_answer(text: str) -> str:
    t = text.lower()
    if "vix" in t:
        return ("**What is VIX?**\n\n"
                "The VIX (CBOE Volatility Index) measures expected 30-day market volatility.\n\n"
                "• VIX **< 15** — Low fear, market complacency\n"
                "• VIX **15–25** — Normal range\n"
                "• VIX **25–35** — Elevated fear\n"
                "• VIX **> 35** — Extreme fear, crisis-level\n\n"
                "When VIX is high, options are more expensive (higher premiums).\n"
                "When VIX is low, options are cheaper.\n\n"
                "Current VIX data is available on the Macro Dashboard.")
    if any(w in t for w in ["inflation", "cpi"]):
        return ("**Inflation Overview**\n\n"
                "Inflation measures how quickly prices rise across the economy.\n\n"
                "• **Moderate (2-3%)** — Normal, healthy for growth\n"
                "• **Elevated (4-6%)** — May trigger Fed rate hikes\n"
                "• **High (>6%)** — Historically unusual, pressures equities\n\n"
                "High inflation tends to:\n"
                "• Pressure growth stock valuations\n"
                "• Benefit value stocks and commodities\n"
                "• Lead to higher interest rates\n\n"
                "Current CPI and PPI data is available on the Macro Dashboard.")
    if any(w in t for w in ["recession", "bear market"]):
        return ("**Recession & Bear Markets**\n\n"
                "A recession is two consecutive quarters of negative GDP growth.\n"
                "A bear market is a 20%+ decline from recent highs.\n\n"
                "**Warning signs include:**\n"
                "• Inverted yield curve\n"
                "• Rising unemployment\n"
                "• Declining corporate profits\n"
                "• Tightening financial conditions\n\n"
                "Defensive sectors (utilities, healthcare, staples) typically outperform during recessions.")
    return ("**Market Conditions**\n\n"
            "The market environment depends on several factors:\n\n"
            "• **Economic data** — GDP, employment, consumer spending\n"
            "• **Monetary policy** — Fed rates, balance sheet\n"
            "• **Earnings** — Corporate profit trends\n"
            "• **Geopolitics** — Trade, regulation, global events\n\n"
            "For real-time market data, check the Macro Dashboard.\n"
            "This analysis is educational — not financial advice.")


def _education_answer(text: str) -> str:
    t = text.lower()
    if "rsi" in t:
        return ("**RSI (Relative Strength Index)**\n\n"
                "RSI is a momentum indicator that ranges from **0 to 100**.\n\n"
                "• **> 70** — Overbought (may be due for pullback)\n"
                "• **< 30** — Oversold (may be due for bounce)\n"
                "• **30–70** — Neutral range\n\n"
                "RSI measures the speed and change of price movements.\n"
                "It works best with other indicators like MACD and moving averages.")
    if "beta" in t:
        return ("**Beta**\n\n"
                "Beta measures a stock's volatility relative to the market (SPY).\n\n"
                "• **Beta = 1** — Moves with the market\n"
                "• **Beta > 1** — More volatile than market\n"
                "• **Beta < 1** — Less volatile than market\n\n"
                "Example: A beta of 1.5 means the stock tends to move 50% more than the market.")
    if "diversif" in t:
        return ("**Diversification**\n\n"
                "Diversification means spreading investments across different assets to reduce risk.\n\n"
                "• **Across sectors** — Tech, healthcare, finance, energy, etc.\n"
                "• **Across geographies** — US, international, emerging markets\n"
                "• **Across asset classes** — Stocks, bonds, real estate, commodities\n\n"
                "A well-diversified portfolio typically has **10-20+ positions** across **3+ sectors**.")
    if "earnings" in t or "eps" in t:
        return ("**Earnings Reports**\n\n"
                "Companies report earnings quarterly. Key metrics:\n\n"
                "• **EPS** (Earnings Per Share) — Profit divided by shares\n"
                "• **Revenue** — Total sales\n"
                "• **Guidance** — Future outlook from management\n\n"
                "An earnings **beat** (actual > estimate) often lifts the stock.\n"
                "An earnings **miss** (actual < estimate) often drops the stock.\n"
                "IV typically rises before earnings and collapses after (IV crush).")

    return ("**Investing Basics**\n\n"
            "Here are concepts I can explain:\n\n"
            "• **RSI** — Momentum indicator (overbought/oversold)\n"
            "• **MACD** — Trend-following momentum indicator\n"
            "• **Beta** — Volatility vs the market\n"
            "• **Diversification** — Spreading risk\n"
            "• **VIX** — Market fear gauge\n"
            "• **Earnings** — Corporate financial reports\n\n"
            "What would you like to learn about?")


async def _full_ticker_analysis(ticker: str) -> str:
    t = await _ticker_analysis(ticker)
    o = await _options_flow(ticker)
    te = await _technical_analysis(ticker)
    e = await _earnings_analysis(ticker)
    return f"{t}\n\n---\n\n{o}\n\n---\n\n{te}\n\n---\n\n{e}"


def _fallback() -> str:
    return ("I can help you with market and portfolio analysis.\n\n"
            "**Try asking:**\n"
            "• **Analyze NVDA** — Full ticker analysis\n"
            "• **Options strategy for AAPL** — Strategy ideas\n"
            "• **Explain VIX** — Market volatility\n"
            "• **Analyze my portfolio** — Portfolio insights\n"
            "• **Technical analysis for AMD** — RSI, MACD, trends\n\n"
            "What would you like to explore?")
