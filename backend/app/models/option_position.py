import uuid
from datetime import date, datetime
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.base_model import TimestampMixin, UUIDMixin


class OptionPosition(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "option_positions"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    underlying_symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # call | put
    side: Mapped[str] = mapped_column(String(5), nullable=False)  # long | short
    strike_price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    contracts: Mapped[int] = mapped_column(Numeric(10, 0), nullable=False)
    premium_per_contract: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    portfolio = relationship("Portfolio", back_populates="option_positions")

    __table_args__ = (
        CheckConstraint("option_type IN ('call', 'put')", name="ck_option_type"),
        CheckConstraint("side IN ('long', 'short')", name="ck_option_side"),
        CheckConstraint("contracts > 0", name="ck_contracts_positive"),
        CheckConstraint("strike_price > 0", name="ck_strike_positive"),
        CheckConstraint("premium_per_contract >= 0", name="ck_premium_non_negative"),
    )
