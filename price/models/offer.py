from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db

if TYPE_CHECKING:
    from .product import Product
    from .price_history import PriceHistory


class Offer(db.Model):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    external_id: Mapped[str] = mapped_column(
        db.String(150),
        unique=True,
        index=True
    )

    source: Mapped[str] = mapped_column(
        db.String(50)
    )

    title: Mapped[str] = mapped_column(
        db.Text
    )

    url: Mapped[str] = mapped_column(
        db.Text
    )

    image_url: Mapped[str] = mapped_column(
        db.Text
    )

    price: Mapped[float] = mapped_column(
        db.Float
    )

    last_update: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="offers"
    )

    history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="offer",
        cascade="all, delete-orphan"
    )
