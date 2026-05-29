from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    title: Mapped[str] = mapped_column(
        db.String(150)
    )

    message: Mapped[str] = mapped_column(
        db.Text
    )

    sent: Mapped[bool] = mapped_column(
        db.Boolean,
        default=False
    )

    sent_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="notifications"
    )
