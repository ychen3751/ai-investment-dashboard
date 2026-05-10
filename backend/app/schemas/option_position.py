import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class OptionPositionCreate(BaseModel):
    underlying_symbol: str = Field(..., min_length=1, max_length=10)
    option_type: str = Field(..., pattern="^(call|put)$")
    side: str = Field(..., pattern="^(long|short)$")
    strike_price: Decimal = Field(..., gt=0)
    expiration_date: date
    contracts: int = Field(..., gt=0)
    premium_per_contract: Decimal = Field(..., ge=0)


class OptionPositionUpdate(BaseModel):
    contracts: int = Field(..., gt=0)
    premium_per_contract: Decimal = Field(..., ge=0)


class OptionPositionResponse(BaseModel):
    id: uuid.UUID
    underlying_symbol: str
    option_type: str
    side: str
    strike_price: Decimal
    expiration_date: date
    contracts: int
    premium_per_contract: Decimal
    # Computed fields
    cost_basis: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_pct: Optional[float] = None
    current_price: Optional[Decimal] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
