import click
from decimal import Decimal
from price.ext.db import db

from price.ext.cli.security import (
    ensure_safe_seed_environment,
    ensure_safe_drop_environment
)
from price.models.notification import Notification
from price.models.offer import Offer
from price.models.price_history import PriceHistory
from price.models.product import Product
from price.models.user import User
from price.models.product_monitoring import ProductMonitoring


# ======================================
# INIT
# ======================================
def init_app(app):

    # ==================================
    # CREATE DB
    # ==================================
    @app.cli.command("create-db")
    def create_db():

        import price.models

        db.create_all()

        click.echo(
            "Banco criado com sucesso."
        )

    # ==================================
    # DROP DB
    # ==================================

    @app.cli.command("drop-db")
    @click.confirmation_option(
        prompt="Apagar banco inteiro?"
    )
    def drop_db():
        ensure_safe_drop_environment()

        db.drop_all()

        click.echo(
            "Banco removido."
        )

    # ==================================
    # SEED DEV
    # ==================================

    @app.cli.command("seed-dev")
    def seed_dev():

        ensure_safe_seed_environment()

        click.echo(
            "Popular banco? [y/N]: ",
            nl=False
        )

        confirm = input().strip().lower()

        if confirm not in (
            "y",
            "yes",
            "s",
            "sim"
        ):
            click.echo(
                "Cancelado."
            )
            return

        try:

            click.echo(
                "Criando seed..."
            )

            # ==========================
            # USER DEMO
            # ==========================
            user = User.query.filter_by(
                email="pablo@pricealert.dev"
            ).first()

            if not user:

                user = User(
                    name="Pablo",
                    email="pablo@pricealert.dev",
                    password="123",
                )

                db.session.add(
                    user
                )

            db.session.flush()

            # ==========================
            # PRODUTOS
            # ==========================
            rtx = Product(
                google_product_id="g1",
                title="RTX 4060",
                str_current_price="R$ 2.857,27",
                product_token="token_rtx",
                product_shoping_link="https://shopping.google.com/rtx4060",
                image="https://example.com/rtx-4060.jpg",
            )

            ps5 = Product(
                google_product_id="g2",
                title="PS5 Slim",
                str_current_price="R$ 1.614,15 agora",
                product_token="token_ps5",
                product_shoping_link="https://shopping.google.com/ps5",
                image="https://example.com/ps5-slim.jpg",
            )

            iphone = Product(
                google_product_id="g3",
                title="iPhone 13",
                str_current_price="R$ 1.614,15 agora",
                product_token="token_iphone",
                product_shoping_link="https://shopping.google.com/iphone13",
                image="https://example.com/iphone13.jpg",
            )

            db.session.add_all([
                rtx,
                ps5,
                iphone
            ])

            db.session.flush()

            # ==========================
            # OFFERS
            # ==========================
            offer1 = Offer(
                product=rtx,
                merchant="MercadoLivre",
                product_url="https://mercadolivre.com.br/rtx4060",
                affiliate_url="https://mercadolivre.com.br/rtx4060?ref=123",
                current_price=Decimal("1899.00"),
                shipping_price=Decimal("0.00"),
                rating=5,
                reviews_count=42,
            )

            offer2 = Offer(
                product=ps5,
                merchant="MercadoLivre",
                product_url="https://mercadolivre.com.br/ps5",
                affiliate_url=None,
                current_price=Decimal("3199.00"),
                shipping_price=Decimal("25.00"),
                rating=4,
                reviews_count=150,
            )

            db.session.add_all([
                offer1,
                offer2
            ])

            db.session.flush()

            # ==========================
            # HISTÓRICO
            # ==========================
            db.session.add_all([

                PriceHistory(
                    offer=offer1,
                    price=Decimal("1999.00"),
                ),

                PriceHistory(
                    offer=offer1,
                    price=Decimal("1899.00"),
                ),

                PriceHistory(
                    offer=offer2,
                    price=Decimal("3499.00"),
                )

            ])

            # ==========================
            # MONITORAMENTO
            # ==========================
            monitor1 = ProductMonitoring(
                user=user,
                product=rtx,
                desired_price=Decimal("1700.00"),
                notify_only_lowest_price=False,
                is_active=True,
            )

            monitor2 = ProductMonitoring(
                user=user,
                product=ps5,
                desired_price=Decimal("3000.00"),
                last_notified_price=None,
                notify_only_lowest_price=True,
                is_active=True,
            )

            db.session.add_all([
                monitor1,
                monitor2
            ])

            # ==========================
            # ALERTAS
            # ==========================
            notification = Notification(
                user=user,
                product=rtx,
                title="Preço caiu",
                message="RTX 4060 caiu para R$1899",
            )

            db.session.add(
                notification
            )

            db.session.commit()

            click.echo(
                "Seed finalizado."
            )

        except Exception as e:

            db.session.rollback()

            raise click.ClickException(
                str(e)
            )
