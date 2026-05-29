from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db


class UserMonitoring(db.Model):
    __tablename__ = "user_monitorings"

    id: Mapped[int] = mapped_column(
        db.Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    desired_price: Mapped[float] = mapped_column(
        db.Float
    )

    active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="monitorings"
    )

    product = relationship(
        "Product",
        back_populates="monitorings"
    )
