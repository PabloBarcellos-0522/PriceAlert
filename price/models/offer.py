from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db

if TYPE_CHECKING:
    from .product import Product
    from .price_history import PriceHistory


class Offer(db.Model):
    __tablename__ = "offers"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        index=True,
        nullable=False
    )

    merchant: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    product_url: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    affiliate_url: Mapped[Optional[str]] = mapped_column(
        db.String(255),
        nullable=True
    )

    current_price: Mapped[Decimal] = mapped_column(
        db.Numeric(8, 2),
        nullable=False
    )

    shipping_price: Mapped[Optional[Decimal]] = mapped_column(
        db.Numeric(8, 2),
        nullable=True
    )

    rating: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True
    )

    reviews_count: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
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
