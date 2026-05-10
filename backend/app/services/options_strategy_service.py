"""Options strategy recommendation engine — suggests beginner-friendly strategies
based on market outlook, risk tolerance, and capital.

Fully deterministic.  Educational only — not financial advice.
"""
from typing import Any, Dict, Optional

from app.core.config import settings

STRATEGIES = {
    "covered_call": {
        "name": "Covered Call",
        "bias": "bullish_neutral",
        "risk_level": "low",
        "max_profit": "Limited to strike price + premium received",
        "max_loss": "Full stock value (if stock goes to $0)",
        "breakeven": "Stock purchase price - premium received",
        "description": "Sell a call option against stock you already own. Generates income while limiting upside.",
        "beginner_friendly": True,
        "capital_required": "Must own 100 shares per contract",
    },
    "cash_secured_put": {
        "name": "Cash-Secured Put",
        "bias": "bullish",
        "risk_level": "moderate",
        "max_profit": "Premium received",
        "max_loss": "Strike price × 100 - premium received (per contract)",
        "breakeven": "Strike price - premium received",
        "description": "Sell a put option and collect premium. You're obligated to buy shares if assigned, but you get the stock at an effective discount.",
        "beginner_friendly": True,
        "capital_required": "Cash to buy 100 shares per contract",
    },
    "bull_call_spread": {
        "name": "Bull Call Spread",
        "bias": "bullish",
        "risk_level": "moderate",
        "max_profit": "Strike width - net premium paid",
        "max_loss": "Net premium paid",
        "breakeven": "Lower strike + net premium paid",
        "description": "Buy a lower-strike call and sell a higher-strike call. Profits from moderate upside with defined risk.",
        "beginner_friendly": True,
        "capital_required": "Low — defined risk debit spread",
    },
    "bear_put_spread": {
        "name": "Bear Put Spread",
        "bias": "bearish",
        "risk_level": "moderate",
        "max_profit": "Strike width - net premium paid",
        "max_loss": "Net premium paid",
        "breakeven": "Higher strike - net premium paid",
        "description": "Buy a higher-strike put and sell a lower-strike put. Profits from moderate downside with defined risk.",
        "beginner_friendly": True,
        "capital_required": "Low — defined risk debit spread",
    },
    "protective_put": {
        "name": "Protective Put",
        "bias": "bearish_neutral",
        "risk_level": "low",
        "max_profit": "Unlimited (stock can rise indefinitely)",
        "max_loss": "Stock cost - strike price + premium paid",
        "breakeven": "Stock purchase price + premium paid",
        "description": "Buy a put option as insurance for stock you own. Limits downside while keeping upside potential.",
        "beginner_friendly": True,
        "capital_required": "Must own 100 shares + premium per contract",
    },
    "iron_condor": {
        "name": "Iron Condor",
        "bias": "neutral",
        "risk_level": "moderate",
        "max_profit": "Net premium received",
        "max_loss": "Strike width - net premium received",
        "breakeven": "Upper: short call strike + premium; Lower: short put strike - premium",
        "description": "Sell an out-of-the-money call spread and put spread. Profits from the stock staying within a range.",
        "beginner_friendly": False,
        "capital_required": "Moderate — defined risk credit spread",
    },
    "long_call": {
        "name": "Long Call",
        "bias": "bullish",
        "risk_level": "high",
        "max_profit": "Unlimited",
        "max_loss": "Premium paid",
        "breakeven": "Strike price + premium paid",
        "description": "Buy a call option. Profits from upside price movement with limited downside (the premium paid).",
        "beginner_friendly": True,
        "capital_required": "Low — just the premium",
    },
    "long_put": {
        "name": "Long Put",
        "bias": "bearish",
        "risk_level": "high",
        "max_profit": "Strike price × 100 - premium paid (asset goes to $0)",
        "max_loss": "Premium paid",
        "breakeven": "Strike price - premium paid",
        "description": "Buy a put option. Profits from downside price movement with limited risk (the premium paid).",
        "beginner_friendly": True,
        "capital_required": "Low — just the premium",
    },
}


async def recommend_strategy(
    bias: str,
    volatility: str,
    risk_tolerance: str,
    capital: float = 1000,
    time_horizon: str = "medium",
) -> Dict[str, Any]:
    """Recommend the best options strategy based on user inputs."""
    bias = bias.lower()
    volatility = volatility.lower()
    risk_tolerance = risk_tolerance.lower()

    candidates = list(STRATEGIES.values())

    # Filter by bias
    if bias == "bullish":
        candidates = [s for s in candidates if "bullish" in s["bias"]]
    elif bias == "bearish":
        candidates = [s for s in candidates if "bearish" in s["bias"]]
    elif bias == "neutral":
        candidates = [s for s in candidates if s["bias"] == "neutral"]

    # Filter by risk tolerance
    if risk_tolerance == "low":
        candidates = [s for s in candidates if s["risk_level"] == "low"]
    elif risk_tolerance == "moderate":
        candidates = [s for s in candidates if s["risk_level"] in ("low", "moderate")]

    # Prefer beginner-friendly
    candidates.sort(key=lambda s: (not s["beginner_friendly"], ["low", "moderate", "high"].index(s["risk_level"])))

    if not candidates:
        candidates = list(STRATEGIES.values())

    primary = candidates[0]

    # Generate explanation
    explanation = _generate_explanation(primary, bias, volatility, time_horizon)

    # Optional OpenAI enrichment
    ai_explanation = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            prompt = (
                f"Recommend the {primary['name']} strategy for a {bias} outlook "
                f"with {risk_tolerance} risk tolerance. "
                f"Explain in 2-3 sentences. Do NOT give financial advice."
            )
            from app.external.openai_client import chat_query as openai_chat
            result = await openai_chat("OPTIONS", prompt, [])
            if result and "not configured" not in result:
                ai_explanation = result
        except Exception:
            pass

    return {
        "strategy": primary["name"],
        "bias": primary["bias"],
        "risk_level": primary["risk_level"],
        "max_profit": primary["max_profit"],
        "max_loss": primary["max_loss"],
        "breakeven": primary["breakeven"],
        "description": primary["description"],
        "ai_explanation": ai_explanation or explanation,
        "capital_required": primary["capital_required"],
        "beginner_friendly": primary["beginner_friendly"],
    }


def _generate_explanation(strategy: Dict, bias: str, volatility: str, horizon: str) -> str:
    parts = [f"The {strategy['name']} is {'a beginner-friendly' if strategy['beginner_friendly'] else 'an advanced'} strategy."]
    if "bullish" in strategy["bias"] and bias == "bullish":
        parts.append("It aligns with your bullish outlook by profiting from upward price movement.")
    elif "bearish" in strategy["bias"] and bias == "bearish":
        parts.append("It aligns with your bearish outlook by profiting from downward price movement.")
    elif strategy["bias"] == "neutral":
        parts.append("It's designed for a neutral outlook, profiting from the stock staying within a range.")
    else:
        parts.append("It provides portfolio protection while maintaining upside potential.")

    if strategy["risk_level"] == "low":
        parts.append("Risk is limited, making it suitable for conservative investors.")
    elif strategy["risk_level"] == "moderate":
        parts.append("Risk is defined and manageable for most investors.")
    else:
        parts.append("Risk is higher — this strategy requires active monitoring.")

    if horizon == "short" and "call" in strategy["name"].lower():
        parts.append("Short timeframes increase time decay risk — monitor closely.")
    elif horizon == "long" and strategy["beginner_friendly"]:
        parts.append("Longer timeframes reduce time decay pressure, giving the trade more room to work.")

    return " ".join(parts)
