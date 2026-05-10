import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    alert_type: str = Field(..., pattern="^(price_above|price_below|daily_pct_change|volume_surge|rsi_above|rsi_below)$")
    condition: dict


class AlertResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    alert_type: str
    condition: dict
    is_active: bool
    triggered_at: Optional[datetime]
    last_checked_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    condition: Optional[dict] = None
