from openai import AsyncOpenAI
from typing import Any, Dict, List, Optional
from app.core.config import settings

_client: Optional[AsyncOpenAI] = None


def get_client() -> Optional[AsyncOpenAI]:
    global _client
    if _client is None and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "placeholder_openai_api_key":
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def analyze_fundamental(symbol: str, company_name: str, financial_data: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    if not client:
        return {
            "company_summary": "OpenAI API key not configured. Set OPENAI_API_KEY in .env.",
            "strengths": [],
            "weaknesses": [],
            "key_metrics_analysis": {},
            "overall_assessment": "neutral",
            "confidence_score": 0,
        }

    prompt = f"""You are a financial analyst. Analyze {company_name} ({symbol}) using this data:
{financial_data}

Provide analysis as JSON:
{{
  "company_summary": "2-3 sentence overview",
  "strengths": ["list of 3-5 competitive advantages"],
  "weaknesses": ["list of 3-5 risk factors"],
  "key_metrics_analysis": {{"pe_ratio": "interpretation", "profit_margins": "interpretation", "revenue_growth": "interpretation", "debt_levels": "interpretation"}},
  "overall_assessment": "bullish|bearish|neutral",
  "confidence_score": 0-100
}}"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1000,
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"company_summary": "Analysis failed. Please try again.", "overall_assessment": "neutral", "confidence_score": 0}


async def chat_query(symbol: str, question: str, history: List[Dict[str, str]]) -> str:
    client = get_client()
    if not client:
        return "OpenAI API key not configured. Set OPENAI_API_KEY in .env."

    messages = [
        {"role": "system", "content": f"You are a financial analyst helping an investor research {symbol}. Provide concise, data-driven answers."}
    ]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception:
        return "Sorry, I encountered an error. Please try again."
