from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from price.ext.db import db

if TYPE_CHECKING:
    from .product_monitoring import ProductMonitoring
    from .notification import Notification


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False,
        index=True
    )

    password: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
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

    monitorings: Mapped[List["ProductMonitoring"]] = relationship(
        "ProductMonitoring",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.email}>"
