import click
from price.ext.db import db
from price.models import *

from price.ext.cli.security import (
    ensure_safe_seed_environment
)
from price.models.category import Category
from price.models.notification import Notification
from price.models.offer import Offer
from price.models.price_history import PriceHistory
from price.models.product import Product
from price.models.user import User
from price.models.user_monitoring import UserMonitoring


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
            # CATEGORIAS
            # ==========================
            categories_data = [
                ("Hardware", "cpu"),
                ("Celulares", "mobile"),
                ("Games", "gamepad"),
                ("Casa", "house"),
                ("Informática", "desktop")
            ]

            categories = {}

            for name, icon in categories_data:

                category = (
                    Category.query
                    .filter_by(name=name)
                    .first()
                )

                if not category:

                    category = Category(
                        name=name,
                        icon=icon
                    )

                    db.session.add(
                        category
                    )

                categories[name] = category

            db.session.flush()

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
                    password="123"
                )

                db.session.add(
                    user
                )

            db.session.flush()

            # ==========================
            # PRODUTOS
            # ==========================
            rtx = Product(
                canonical_name="RTX 4060",

                category=categories[
                    "Hardware"
                ]
            )

            ps5 = Product(
                canonical_name="PS5 Slim",

                category=categories[
                    "Games"
                ]
            )

            iphone = Product(
                canonical_name="iPhone 13",

                category=categories[
                    "Celulares"
                ]
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

                external_id="MLB123",

                source="MercadoLivre",

                title="RTX 4060 ASUS Dual",

                price=1899,

                url="https://...",

                image_url="https://example.com/rtx-4060.jpg"

            )

            offer2 = Offer(

                product=ps5,

                external_id="MLB456",

                source="MercadoLivre",

                title="PS5 Slim",

                price=3199,

                url="https://...",

                image_url="https://example.com/ps5-slim.jpg"

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
                    price=1999
                ),

                PriceHistory(
                    offer=offer1,
                    price=1899
                ),

                PriceHistory(
                    offer=offer2,
                    price=3499
                )

            ])

            # ==========================
            # MONITORAMENTO
            # ==========================
            monitor1 = UserMonitoring(

                user=user,

                product=rtx,

                desired_price=1700
            )

            monitor2 = UserMonitoring(

                user=user,

                product=ps5,

                desired_price=3000
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

                title="Preço caiu",

                message="RTX 4060 caiu para R$1899",

                sent=True
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
