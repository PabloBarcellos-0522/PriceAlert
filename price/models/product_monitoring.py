from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func
from price.ext.db import db


class ProductMonitoring(db.Model):
    __tablename__ = "product_monitorings"
    __table_args__ = {'extend_existing': True}

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

    desired_price: Mapped[Optional[Decimal]] = mapped_column(
        db.Numeric(8, 2),
        index=True,
        nullable=True
    )

    last_notified_price: Mapped[Optional[Decimal]] = mapped_column(
        db.Numeric(8, 2),
        nullable=True
    )

    notify_only_lowest_price: Mapped[bool] = mapped_column(
        db.Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        db.Boolean,
        default=True,
        index=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        db.DateTime(timezone=True),
        nullable=False,
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

    @property
    def nome(self) -> str:
        return self.product.title if self.product else ""

    @property
    def imagem_url(self) -> str:
        return self.product.image if self.product else ""

    @property
    def preco_atual(self) -> float:
        if self.product and self.product.offers:
            best_offer = min(self.product.offers, key=lambda o: o.current_price)
            return float(best_offer.current_price)
        return 0.0

    @property
    def loja_nome(self) -> str:
        if self.product and self.product.offers:
            best_offer = min(self.product.offers, key=lambda o: o.current_price)
            return best_offer.merchant
        return "N/A"

    @property
    def preco_alvo(self) -> float:
        return float(self.desired_price) if self.desired_price else 0.0

