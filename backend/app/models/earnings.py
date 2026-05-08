import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.base_model import UUIDMixin, TimestampMixin


class EarningsCalendar(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "earnings_calendar"

    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fiscal_quarter: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    fiscal_year: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    eps_estimate: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    revenue_estimate: Mapped[float] = mapped_column(Numeric(18, 2), nullable=True)
    whisper_number: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "report_date", name="uq_earnings_calendar_symbol_date"),
    )


class EarningsReport(UUIDMixin, Base):
    __tablename__ = "earnings_reports"

    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_quarter: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    eps_actual: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    eps_estimate: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    revenue_actual: Mapped[float] = mapped_column(Numeric(18, 2), nullable=True)
    revenue_estimate: Mapped[float] = mapped_column(Numeric(18, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "fiscal_quarter", "fiscal_year", name="uq_earnings_reports_symbol_q"),
    )
