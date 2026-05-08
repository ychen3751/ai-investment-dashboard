import uuid
from datetime import date
from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.base_model import UUIDMixin, TimestampMixin


class Transaction(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(4), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    commission: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    portfolio = relationship("Portfolio", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("transaction_type IN ('BUY', 'SELL')", name="ck_transaction_type"),
    )
