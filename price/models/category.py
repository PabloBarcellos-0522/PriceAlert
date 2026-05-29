from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from price.ext.db import db

if TYPE_CHECKING:
    from .product import Product


class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        db.String(50),
        unique=True
    )

    icon: Mapped[str] = mapped_column(
        db.String(50)
    )

    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category"
    )
