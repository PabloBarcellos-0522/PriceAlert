from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from price.ext.db import db

if TYPE_CHECKING:
    from .offer import Offer
    from .product_monitoring import ProductMonitoring
    from .notification import Notification


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    google_product_id: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True
    )

    str_current_price: Mapped[Optional[str]] = mapped_column(
        db.String(50),
        nullable=True
    )

    rating: Mapped[Optional[float]] = mapped_column(
        db.Integer,
        nullable=True
    )

    review_count: Mapped[Optional[int]] = mapped_column(
        db.Integer,
        nullable=True
    )

    product_token: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True
    )

    product_shoping_link: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True
    )

    image: Mapped[Optional[str]] = mapped_column(
        db.Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )

    offers: Mapped[List["Offer"]] = relationship(
        "Offer",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    monitorings: Mapped[List["ProductMonitoring"]] = relationship(
        "ProductMonitoring",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    @property
    def nome(self) -> str:
        return self.title

    @property
    def imagem_url(self) -> str:
        return self.image or ""

    @property
    def preco_atual(self) -> float:
        if self.offers:
            best_offer = min(self.offers, key=lambda o: o.current_price)
            return float(best_offer.current_price)
        return 0.0

    @property
    def loja_nome(self) -> str:
        if self.offers:
            best_offer = min(self.offers, key=lambda o: o.current_price)
            return best_offer.merchant
        return "N/A"
