import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class WatchlistItemResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    notes: Optional[str]
    added_at: datetime
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None

    model_config = {"from_attributes": True}


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    item_count: int = 0
    items: List[WatchlistItemResponse] = []

    model_config = {"from_attributes": True}


class WatchlistItemCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    notes: Optional[str] = None
