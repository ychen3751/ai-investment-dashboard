import uuid
from datetime import datetime
from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class MarketIndex(Base):
    __tablename__ = "market_indices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    daily_change: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    daily_change_pct: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SectorPerformance(Base):
    __tablename__ = "sector_performances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sector_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    daily_change_pct: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    ytd_change_pct: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    indicator_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    previous_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
