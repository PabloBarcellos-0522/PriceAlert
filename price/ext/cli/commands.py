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
            from datetime import datetime, timedelta

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

            # Limpar dados antigos para ter um seed limpo se solicitado
            click.echo("Limpando dados de monitoramento e ofertas anteriores...")
            Notification.query.delete()
            ProductMonitoring.query.delete()
            PriceHistory.query.delete()
            Offer.query.delete()
            Product.query.delete()
            db.session.flush()

            # ==========================
            # PRODUTOS com imagens reais do Unsplash
            # ==========================
            rtx = Product(
                google_product_id="g1",
                title="Placa de Vídeo NVIDIA RTX 4060 8GB",
                str_current_price="R$ 1.849,00",
                product_token="token_rtx",
                product_shoping_link="https://shopping.google.com/rtx4060",
                image="https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=300&auto=format&fit=crop&q=60",
            )

            ps5 = Product(
                google_product_id="g2",
                title="Console PlayStation 5 Slim 1TB",
                str_current_price="R$ 3.499,00",
                product_token="token_ps5",
                product_shoping_link="https://shopping.google.com/ps5",
                image="https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=300&auto=format&fit=crop&q=60",
            )

            iphone = Product(
                google_product_id="g3",
                title="Apple iPhone 13 128GB Estelar",
                str_current_price="R$ 3.249,00",
                product_token="token_iphone",
                product_shoping_link="https://shopping.google.com/iphone13",
                image="https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=300&auto=format&fit=crop&q=60",
            )

            db.session.add_all([rtx, ps5, iphone])
            db.session.flush()

            # ==========================
            # OFFERS (3 lojas para cada produto)
            # ==========================
            # RTX 4060 Offers
            rtx_pichau = Offer(
                product=rtx,
                merchant="Pichau",
                product_url="https://pichau.com.br/rtx4060",
                affiliate_url="https://pichau.com.br/rtx4060?ref=pricealert",
                current_price=Decimal("1849.00"),
                shipping_price=Decimal("22.00"),
                rating=5,
                reviews_count=67
            )
            rtx_kabum = Offer(
                product=rtx,
                merchant="Kabum",
                product_url="https://kabum.com.br/rtx4060",
                affiliate_url="https://kabum.com.br/rtx4060?ref=pricealert",
                current_price=Decimal("1859.00"),
                shipping_price=Decimal("19.90"),
                rating=5,
                reviews_count=125
            )
            rtx_terabyte = Offer(
                product=rtx,
                merchant="Terabyte",
                product_url="https://terabyteshop.com.br/rtx4060",
                affiliate_url=None,
                current_price=Decimal("1899.00"),
                shipping_price=Decimal("15.00"),
                rating=4,
                reviews_count=84
            )

            # PS5 Offers
            ps5_amazon = Offer(
                product=ps5,
                merchant="Amazon",
                product_url="https://amazon.com.br/ps5",
                affiliate_url="https://amazon.com.br/ps5?tag=pricealert-20",
                current_price=Decimal("3499.00"),
                shipping_price=Decimal("0.00"),  # Grátis
                rating=5,
                reviews_count=1420
            )
            ps5_ml = Offer(
                product=ps5,
                merchant="Mercado Livre",
                product_url="https://mercadolivre.com.br/ps5",
                affiliate_url=None,
                current_price=Decimal("3550.00"),
                shipping_price=Decimal("0.00"),
                rating=4,
                reviews_count=890
            )
            ps5_magalu = Offer(
                product=ps5,
                merchant="Magazine Luiza",
                product_url="https://magazineluiza.com.br/ps5",
                affiliate_url="https://magazineluiza.com.br/ps5?ref=pricealert",
                current_price=Decimal("3699.00"),
                shipping_price=Decimal("29.90"),
                rating=5,
                reviews_count=320
            )

            # iPhone Offers
            iphone_fast = Offer(
                product=iphone,
                merchant="Fast Shop",
                product_url="https://fastshop.com.br/iphone13",
                affiliate_url="https://fastshop.com.br/iphone13?ref=pricealert",
                current_price=Decimal("3249.00"),
                shipping_price=Decimal("19.00"),
                rating=5,
                reviews_count=180
            )
            iphone_ml = Offer(
                product=iphone,
                merchant="Mercado Livre",
                product_url="https://mercadolivre.com.br/iphone13",
                affiliate_url=None,
                current_price=Decimal("3299.00"),
                shipping_price=Decimal("0.00"),
                rating=5,
                reviews_count=2050
            )
            iphone_bahia = Offer(
                product=iphone,
                merchant="Casas Bahia",
                product_url="https://casasbahia.com.br/iphone13",
                affiliate_url=None,
                current_price=Decimal("3399.00"),
                shipping_price=Decimal("12.00"),
                rating=4,
                reviews_count=450
            )

            db.session.add_all([
                rtx_pichau, rtx_kabum, rtx_terabyte,
                ps5_amazon, ps5_ml, ps5_magalu,
                iphone_fast, iphone_ml, iphone_bahia
            ])
            db.session.flush()

            # ==========================
            # HISTÓRICO DE PREÇOS (Simulando varreduras nos últimos dias)
            # ==========================
            now = datetime.now()
            db.session.add_all([
                # Pichau RTX 4060
                PriceHistory(offer=rtx_pichau, price=Decimal("2099.00"), captured_at=now - timedelta(days=10)),
                PriceHistory(offer=rtx_pichau, price=Decimal("1999.00"), captured_at=now - timedelta(days=7)),
                PriceHistory(offer=rtx_pichau, price=Decimal("1899.00"), captured_at=now - timedelta(days=4)),

                # Kabum RTX 4060
                PriceHistory(offer=rtx_kabum, price=Decimal("1959.00"), captured_at=now - timedelta(days=8)),
                PriceHistory(offer=rtx_kabum, price=Decimal("1919.00"), captured_at=now - timedelta(days=5)),
                PriceHistory(offer=rtx_kabum, price=Decimal("1879.00"), captured_at=now - timedelta(days=2)),

                # Amazon PS5
                PriceHistory(offer=ps5_amazon, price=Decimal("3799.00"), captured_at=now - timedelta(days=15)),
                PriceHistory(offer=ps5_amazon, price=Decimal("3699.00"), captured_at=now - timedelta(days=10)),
                PriceHistory(offer=ps5_amazon, price=Decimal("3599.00"), captured_at=now - timedelta(days=5)),

                # Fast Shop iPhone
                PriceHistory(offer=iphone_fast, price=Decimal("3499.00"), captured_at=now - timedelta(days=12)),
                PriceHistory(offer=iphone_fast, price=Decimal("3399.00"), captured_at=now - timedelta(days=8)),
                PriceHistory(offer=iphone_fast, price=Decimal("3299.00"), captured_at=now - timedelta(days=3)),
            ])

            # ==========================
            # MONITORAMENTOS DO USUÁRIO
            # ==========================
            monitor_rtx = ProductMonitoring(
                user=user,
                product=rtx,
                desired_price=Decimal("1860.00"),  # Pichau e Kabum atingiram o alvo!
                last_notified_price=Decimal("1859.00"),
                notify_only_lowest_price=False,
                is_active=True,
            )

            monitor_ps5 = ProductMonitoring(
                user=user,
                product=ps5,
                desired_price=Decimal("3500.00"),  # Amazon atingiu o alvo!
                last_notified_price=Decimal("3499.00"),
                notify_only_lowest_price=False,
                is_active=True,
            )

            monitor_iphone = ProductMonitoring(
                user=user,
                product=iphone,
                desired_price=Decimal("3100.00"),  # Alvo ainda não atingido
                last_notified_price=None,
                notify_only_lowest_price=False,
                is_active=True,
            )

            db.session.add_all([monitor_rtx, monitor_ps5, monitor_iphone])
            db.session.flush()

            # ==========================
            # NOTIFICAÇÕES ENVIADAS ANTERIORMENTE
            # ==========================
            db.session.add_all([
                Notification(
                    user=user,
                    product=rtx,
                    title="Preço alvo atingido! 🎯",
                    message="Placa de Vídeo NVIDIA RTX 4060 8GB chegou a R$1849.00 na Pichau!",
                    sent_at=now - timedelta(hours=6)
                ),
                Notification(
                    user=user,
                    product=ps5,
                    title="Preço alvo atingido! 🎯",
                    message="Console PlayStation 5 Slim 1TB chegou a R$3499.00 na Amazon!",
                    sent_at=now - timedelta(days=1)
                ),
                Notification(
                    user=user,
                    product=rtx,
                    title="Menor preço registrado! 💰",
                    message="Placa de Vídeo NVIDIA RTX 4060 8GB com novo menor preço: R$1859.00 na Kabum!",
                    sent_at=now - timedelta(days=2)
                )
            ])

            db.session.commit()

            click.echo(
                "Seed finalizado com sucesso."
            )

        except Exception as e:

            db.session.rollback()

            raise click.ClickException(
                str(e)
            )
