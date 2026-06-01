from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from price.ext.db import db

if TYPE_CHECKING:
    from .offer import Offer
    from .product_monitoring import ProductMonitoring
    from .notification import Notification


class Product(db.Model):
    __tablename__ = "products"

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

    brand: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    product_token: Mapped[str] = mapped_column(
        db.Text,
        nullable=False
    )

    product_shoping_link: Mapped[str] = mapped_column(
        db.Text,
        nullable=False
    )

    image: Mapped[str] = mapped_column(
        db.Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False
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
