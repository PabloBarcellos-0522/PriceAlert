from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db

if TYPE_CHECKING:
    from .offer import Offer
    from .category import Category
    from .user_monitoring import UserMonitoring


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    canonical_name: Mapped[str] = mapped_column(
        db.String(150),
        index=True
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id")
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products"
    )

    offers: Mapped[List["Offer"]] = relationship(
        "Offer",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    monitorings: Mapped[List["UserMonitoring"]] = relationship(
        "UserMonitoring",
        back_populates="product"
    )
