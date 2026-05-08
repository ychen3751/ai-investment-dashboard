from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    symbol: str
    analysis: Dict[str, Any]
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, Any]] = []


class SentimentResponse(BaseModel):
    symbol: str
    sentiment_score: float
    articles: List[Dict[str, Any]] = []
