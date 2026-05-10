"""Options flow analysis — aggregate metrics and rule-based signal interpretation.

Takes every contract from the option chain and computes a comprehensive picture
of options flow: call/put skew, premium concentration, unusual activity, and
volatility.  A deterministic rule engine generates the signal (bullish, bearish,
neutral, mixed) with supporting factors — no LLM required.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.external import openai_client
from app.services import market_data_service
from app.services.options_chain_service import get_chain_with_scores

CONTRACT_MULTIPLIER = 100


async def get_flow_analysis(symbol: str) -> Dict[str, Any]:
    """Full options flow analysis for a symbol.

    Returns structured metrics, bullish/bearish factors, and an overall signal.
    """
    # Fetch all contracts across ALL expirations (use nearest ~4 weeks)
    chain = await get_chain_with_scores(symbol, min_premium=0)
    all_contracts = chain.get("contracts", [])
    underlying = chain.get("underlying_price", 0)

    if not all_contracts:
        return {
            "symbol": symbol.upper(),
            "overall_signal": "neutral",
            "confidence": 0,
            "summary": "Options chain data unavailable for this symbol.",
            "key_metrics": {},
            "top_unusual_contracts": [],
            "bullish_factors": [],
            "bearish_factors": [],
            "risk_factors": [],
        }

    # ── Aggregate metrics ──────────────────────────────────────────────
    calls = [c for c in all_contracts if c.get("option_type") == "call"]
    puts = [c for c in all_contracts if c.get("option_type") == "put"]

    call_vol = sum(c.get("volume", 0) or 0 for c in calls)
    put_vol = sum(c.get("volume", 0) or 0 for c in puts)
    call_prem = sum(c.get("premium", 0) or 0 for c in calls)
    put_prem = sum(c.get("premium", 0) or 0 for c in puts)
    call_oi = sum(c.get("open_interest", 0) or 0 for c in calls)
    put_oi = sum(c.get("open_interest", 0) or 0 for c in puts)

    cp_vol_ratio = round(call_vol / max(put_vol, 1), 2)
    cp_prem_ratio = round(call_prem / max(put_prem, 1), 2)
    cp_oi_ratio = round(call_oi / max(put_oi, 1), 2)

    unusual = [c for c in all_contracts if c.get("unusual_score", 0) >= 30]
    unusual_vol = sum(c.get("volume", 0) or 0 for c in unusual)
    unusual_prem = sum(c.get("premium", 0) or 0 for c in unusual)

    ivs = [c.get("implied_volatility", 0) or 0 for c in all_contracts if (c.get("implied_volatility") or 0) > 0]
    avg_iv = round(sum(ivs) / max(len(ivs), 1), 2) if ivs else None
    max_iv = round(max(ivs), 2) if ivs else None

    today = date.today()

    # Near-term (≤14 days) concentration
    def days_to_exp(c: Dict) -> Optional[int]:
        exp = c.get("expiration", "")
        if exp:
            try:
                ed = datetime.strptime(exp[:10], "%Y-%m-%d").date()
                return (ed - today).days
            except Exception:
                return None
        return None

    near_term_prem = 0
    total_prem = 0

    for c in all_contracts:
        prem = c.get("premium", 0) or 0
        total_prem += prem
        dte = days_to_exp(c)
        if dte is not None and 0 <= dte <= 14:
            near_term_prem += prem

    near_term_pct = round(near_term_prem / max(total_prem, 1) * 100, 1)

    # Near-the-money concentration (≤5% from underlying)
    atm_prem = 0
    for c in all_contracts:
        prem = c.get("premium", 0) or 0
        strike = c.get("strike", 0) or 1
        if underlying > 0:
            moneyness = abs(strike - underlying) / underlying
            if moneyness <= 0.05:
                atm_prem += prem
    atm_pct = round(atm_prem / max(total_prem, 1) * 100, 1)

    # Top unusual contracts (top 5 by score)
    top_unusual = sorted(unusual, key=lambda x: x["unusual_score"], reverse=True)[:5]
    top_unusual_clean = [
        {
            "option_type": c["option_type"],
            "strike": c["strike"],
            "volume": c["volume"],
            "premium": c["premium"],
            "volume_oi_ratio": c["volume_oi_ratio"],
            "unusual_score": c["unusual_score"],
            "signal": c["signal"],
        }
        for c in top_unusual
    ]

    metrics = {
        "call_volume": call_vol,
        "put_volume": put_vol,
        "call_put_volume_ratio": cp_vol_ratio,
        "call_premium": round(call_prem, 2),
        "put_premium": round(put_prem, 2),
        "call_put_premium_ratio": cp_prem_ratio,
        "call_put_oi_ratio": cp_oi_ratio,
        "unusual_count": len(unusual),
        "unusual_volume": unusual_vol,
        "unusual_premium": round(unusual_prem, 2),
        "avg_implied_volatility": avg_iv,
        "max_implied_volatility": max_iv,
        "near_term_premium_pct": near_term_pct,
        "atm_premium_pct": atm_pct,
        "total_premium": round(total_prem, 2),
        "total_contracts": len(all_contracts),
        "call_count": len(calls),
        "put_count": len(puts),
    }

    # ── Rule engine: generate factors and signal ───────────────────────
    bullish_factors: List[str] = []
    bearish_factors: List[str] = []
    risk_factors: List[str] = []
    overall_signal: str = "neutral"
    confidence: int = 0

    # --- Call/Put volume skew ---
    if cp_vol_ratio > 1.5:
        bullish_factors.append(f"Call volume is {cp_vol_ratio:.1f}x put volume — strong call-side activity")
    elif cp_vol_ratio < 0.7:
        bearish_factors.append(f"Put volume exceeds calls ({cp_vol_ratio:.1f}x) — bearish positioning")

    # --- Premium skew ---
    if cp_prem_ratio > 2.0:
        bullish_factors.append(f"Call premium is {cp_prem_ratio:.1f}x put premium — significant capital flowing into calls")
    elif cp_prem_ratio < 0.5:
        bearish_factors.append(f"Put premium dominates ({cp_prem_ratio:.1f}x) — defensive positioning")

    # --- Open interest skew ---
    if cp_oi_ratio > 1.5:
        bullish_factors.append(f"Open interest favors calls ({cp_oi_ratio:.1f}x) — established bullish positioning")
    elif cp_oi_ratio < 0.7:
        bearish_factors.append(f"Open interest favors puts ({cp_oi_ratio:.1f}x) — established bearish positioning")

    # --- Unusual activity ---
    if unusual_vol > 10000:
        bullish_factors.append(f"{len(unusual)} unusual contracts detected ({unusual_vol:,} contracts) — significant abnormal flow")
    elif unusual_vol > 1000:
        bullish_factors.append(f"{len(unusual)} unusual contracts with above-average volume/OI ratios")

    # --- Near-term concentration ---
    if near_term_pct > 50:
        risk_factors.append(f"{near_term_pct}% of premium is in near-term options (≤14 DTE) — elevated time decay risk")
    elif near_term_pct > 30:
        risk_factors.append(f"{near_term_pct}% of premium in near-term options — moderate time decay exposure")

    # --- ATM concentration ---
    if atm_pct > 40:
        bullish_factors.append(f"{atm_pct}% of premium is near-the-money — traders positioning for directional moves")
    elif atm_pct < 10 and total_prem > 1_000_000:
        bearish_factors.append("Premium concentrated in far OTM strikes — speculative flow, not conviction")

    # --- IV analysis ---
    if avg_iv and avg_iv > 60:
        risk_factors.append(f"Elevated implied volatility ({avg_iv:.0f}% avg, {max_iv:.0f}% max) — options are expensive; IV crush risk")
    elif avg_iv and avg_iv < 25:
        bullish_factors.append(f"Low implied volatility ({avg_iv:.0f}%) — options are cheap; favorable for premium buyers")

    # --- High premium trades ---
    high_prem = [c for c in all_contracts if (c.get("premium", 0) or 0) > 500_000]
    if high_prem:
        high_call = sum(1 for c in high_prem if c.get("option_type") == "call")
        high_put = sum(1 for c in high_prem if c.get("option_type") == "put")
        if high_call > high_put:
            bullish_factors.append(f"{high_call} large call trades (>$500K premium each) — institutional-sized bullish flow")
        elif high_put > high_call:
            bearish_factors.append(f"{high_put} large put trades (>$500K premium each) — institutional-sized bearish flow")

    # --- Speculative OTM calls (weekly, far OTM) ---
    otm_calls = [
        c for c in calls
        if c.get("volume", 0) > 0 and underlying > 0 and c.get("strike", 0) > underlying * 1.1
    ]
    if otm_calls:
        otm_call_vol = sum(c.get("volume", 0) or 0 for c in otm_calls)
        otm_call_prem = sum(c.get("premium", 0) or 0 for c in otm_calls)
        if otm_call_vol > 5000:
            bullish_factors.append(f"{otm_call_vol:,} OTM call contracts traded — speculative bullish flow")
            risk_factors.append(f"Significant OTM call volume ({otm_call_prem:,.0f} premium) — lotto-style speculation risk")

    # --- OTM puts (hedging) ---
    otm_puts = [
        c for c in puts
        if c.get("volume", 0) > 0 and underlying > 0 and c.get("strike", 0) < underlying * 0.95
    ]
    if otm_puts:
        otm_put_vol = sum(c.get("volume", 0) or 0 for c in otm_puts)
        if otm_put_vol > 5000:
            bearish_factors.append(f"{otm_put_vol:,} OTM put contracts — hedging or bearish speculation")

    # --- Mixed signals ---
    if len(bullish_factors) >= 2 and len(bearish_factors) >= 2:
        overall_signal = "mixed"
        confidence = 50
    elif len(bullish_factors) >= len(bearish_factors) + 2 and len(bullish_factors) >= 3:
        overall_signal = "bullish"
        confidence = min(95, 50 + len(bullish_factors) * 10 - len(bearish_factors) * 5)
    elif len(bearish_factors) >= len(bullish_factors) + 2 and len(bearish_factors) >= 3:
        overall_signal = "bearish"
        confidence = min(95, 50 + len(bearish_factors) * 10 - len(bullish_factors) * 5)
    elif len(bullish_factors) > len(bearish_factors):
        overall_signal = "bullish"
        confidence = 35 + len(bullish_factors) * 8
    elif len(bearish_factors) > len(bullish_factors):
        overall_signal = "bearish"
        confidence = 35 + len(bearish_factors) * 8
    else:
        overall_signal = "neutral"
        confidence = 30

    confidence = max(10, min(95, confidence))

    # ── Generate summary ───────────────────────────────────────────────
    summary = _generate_summary(overall_signal, confidence, metrics, bullish_factors, bearish_factors)

    # ── Optional OpenAI enrichment ─────────────────────────────────────
    ai_summary = None
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        try:
            prompt = (
                f"Options flow analysis for {symbol.upper()}: "
                f"signal={overall_signal}, confidence={confidence}, "
                f"call_vol={call_vol}, put_vol={put_vol}, "
                f"call_premium={call_prem:.0f}, put_premium={put_prem:.0f}, "
                f"bullish_factors={bullish_factors}, bearish_factors={bearish_factors}, "
                f"risk_factors={risk_factors}. "
                f"Write a 2-3 sentence professional options flow summary. "
                f"Do NOT give financial advice. Be concise and data-driven."
            )
            from app.external.openai_client import chat_query as openai_chat
            ai_result = await openai_chat(symbol.upper(), prompt, [])
            if ai_result and "not configured" not in ai_result:
                ai_summary = ai_result
        except Exception:
            pass

    return {
        "symbol": symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "overall_signal": overall_signal,
        "confidence": confidence,
        "summary": summary,
        "ai_summary": ai_summary,
        "bullish_factors": bullish_factors,
        "bearish_factors": bearish_factors,
        "risk_factors": risk_factors,
        "key_metrics": metrics,
        "top_unusual_contracts": top_unusual_clean,
    }


def _generate_summary(
    signal: str,
    confidence: int,
    metrics: Dict[str, Any],
    bullish: List[str],
    bearish: List[str],
) -> str:
    """Deterministic rule-based summary — never gives financial advice."""
    cp_ratio = metrics.get("call_put_premium_ratio", 1)
    unusual = metrics.get("unusual_count", 0)
    total_prem = metrics.get("total_premium", 0)
    iv = metrics.get("avg_implied_volatility")

    parts = []

    if signal == "bullish":
        parts.append(f"Flow is bullish with {confidence}% confidence.")
        if cp_ratio > 2:
            parts.append(f"Call premium is {cp_ratio:.1f}x puts, suggesting directional call buying.")
        if unusual > 5:
            parts.append(f"{unusual} unusual contracts indicate non-standard flow.")
    elif signal == "bearish":
        parts.append(f"Flow is bearish with {confidence}% confidence.")
        if cp_ratio < 0.5:
            parts.append(f"Put premium is {1/cp_ratio:.1f}x calls, suggesting defensive positioning.")
        if unusual > 5:
            parts.append(f"{unusual} unusual contracts detected.")
    elif signal == "mixed":
        parts.append(f"Flow is mixed ({confidence}% confidence) — conflicting signals from calls and puts.")
    else:
        parts.append(f"Flow is neutral — no strong directional conviction detected.")

    if total_prem > 5_000_000:
        parts.append(f"Total premium of ${total_prem:,.0f} indicates significant options activity.")
    if iv and iv > 50:
        parts.append(f"IV is elevated at {iv:.0f}%, suggesting elevated uncertainty or event risk.")

    return " ".join(parts)
