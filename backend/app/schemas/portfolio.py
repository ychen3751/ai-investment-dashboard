import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: Decimal = Field(..., gt=0)
    average_cost_basis: Decimal = Field(..., gt=0)


class HoldingResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    quantity: Decimal
    average_cost_basis: Decimal
    current_price: Optional[Decimal] = None
    day_change: Optional[Decimal] = None
    day_change_pct: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    total_pnl: Optional[Decimal] = None
    total_pnl_pct: Optional[Decimal] = None
    allocation_pct: Optional[float] = None

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    transaction_type: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    commission: Decimal = Field(default=Decimal("0"), ge=0)
    transaction_date: date
    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    symbol: str
    transaction_type: str
    quantity: Decimal
    price: Decimal
    commission: Decimal
    transaction_date: date
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_value: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    total_pnl: Optional[Decimal] = None
    total_pnl_pct: Optional[float] = None
    holding_count: int = 0

    model_config = {"from_attributes": True}


class PerformanceResponse(BaseModel):
    total_return_pct: Optional[float] = None
    annualized_return_pct: Optional[float] = None
    volatility_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    total_value: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    total_pnl: Optional[Decimal] = None


class PortfolioSummary(BaseModel):
    total_value: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    total_pnl_pct: float = 0
    day_pnl: Decimal = Decimal("0")
    portfolio_count: int = 0
    holding_count: int = 0
