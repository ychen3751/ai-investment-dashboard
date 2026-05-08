import uuid
from datetime import date, datetime
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.base_model import UUIDMixin


class OptionsFlow(UUIDMixin, Base):
    __tablename__ = "options_flow"

    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)
    strike_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    premium: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)
    open_interest: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_oi_ratio: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    unusual_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("option_type IN ('CALL', 'PUT')", name="ck_option_type"),
    )
