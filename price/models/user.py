from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func
from price.ext.db import db

if TYPE_CHECKING:
    from .user_monitoring import UserMonitoring
    from .notification import Notification


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        db.String(100),
        index=True
    )

    email: Mapped[str] = mapped_column(
        db.String(100),
        unique=True,
        index=True
    )

    password: Mapped[str] = mapped_column(
        db.String(255)
    )

    receive_email: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True
    )

    receive_whatsapp: Mapped[bool] = mapped_column(
        db.Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        nullable=False
    )

    monitorings: Mapped[List["UserMonitoring"]] = relationship(
        "UserMonitoring",
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
