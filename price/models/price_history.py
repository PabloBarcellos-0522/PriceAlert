from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db


class PriceHistory(db.Model):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id")
    )

    price: Mapped[float] = mapped_column(
        db.Float
    )

    captured_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    offer = relationship(
        "Offer",
        back_populates="history"
    )
