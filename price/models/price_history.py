from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from price.ext.db import db


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id"),
        index=True,
        nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        db.Numeric(8, 2),
        nullable=False
    )

    captured_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False
    )

    offer = relationship(
        "Offer",
        back_populates="history"
    )
