from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from price.ext.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        index=True,
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        db.String(255),
        nullable=False
    )

    sent_at: Mapped[datetime] = mapped_column(
        db.DateTime,
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="notifications"
    )

    product = relationship(
        "Product",
        back_populates="notifications"
    )
