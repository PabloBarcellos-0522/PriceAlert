from decimal import Decimal
from datetime import datetime
from price.ext.db import db
from price.models.product import Product
from price.models.user import User
from price.models.product_monitoring import ProductMonitoring
from price.models.notification import Notification
from price.models.offer import Offer
from price.models.price_history import PriceHistory


class MonitoringService:
    """Gerencia monitoramento de produtos pelos usuários"""

    def create_monitoring(
        self,
        user: User,
        product: Product,
        desired_price: Decimal = None,
        notify_only_lowest_price: bool = False
    ) -> ProductMonitoring:
        """Cria um novo monitoramento de produto para um usuário"""

        # Verifica se já está monitorando
        existing = ProductMonitoring.query.filter_by(
            user_id=user.id,
            product_id=product.id
        ).first()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.desired_price = desired_price
                existing.notify_only_lowest_price = notify_only_lowest_price
                db.session.commit()
            return existing

        monitoring = ProductMonitoring(
            user=user,
            product=product,
            desired_price=desired_price,
            notify_only_lowest_price=notify_only_lowest_price,
            is_active=True
        )

        db.session.add(monitoring)
        db.session.commit()
        return monitoring

    def stop_monitoring(self, monitoring: ProductMonitoring) -> None:
        """Para o monitoramento de um produto"""
        monitoring.is_active = False
        db.session.commit()

    def check_and_notify(self, monitoring: ProductMonitoring) -> list[Notification]:
        """
        Verifica se preços caíram e cria notificações se necessário

        Regras:
        - Se tem desired_price, notifica quando atinge
        - Se notify_only_lowest_price=True, notifica apenas se é o menor preço já registrado
        - Não notifica de novo se já notificou neste preço
        """
        notifications = []
        product = monitoring.product

        # Obtém o menor preço atual entre todos os offers
        best_offer = self._get_best_offer(product)

        if not best_offer:
            return notifications

        current_price = best_offer.current_price
        last_notified_price = monitoring.last_notified_price

        # Caso 1: Usuário definiu preço desejado
        if monitoring.desired_price:
            if current_price <= monitoring.desired_price:
                if last_notified_price is None or current_price < last_notified_price:
                    notification = self._create_notification(
                        monitoring,
                        best_offer,
                        current_price,
                        "desired_price"
                    )
                    notifications.append(notification)
                    monitoring.last_notified_price = current_price

        # Caso 2: Notificar apenas no menor preço histórico
        elif monitoring.notify_only_lowest_price:
            lowest_historical = self._get_lowest_historical_price(best_offer)

            if current_price < lowest_historical:
                if last_notified_price is None or current_price < last_notified_price:
                    notification = self._create_notification(
                        monitoring,
                        best_offer,
                        current_price,
                        "lowest_price"
                    )
                    notifications.append(notification)
                    monitoring.last_notified_price = current_price

        db.session.commit()
        return notifications

    def check_all_active_monitorings(self) -> list[Notification]:
        """Verifica todos os monitoramentos ativos e cria notificações"""
        all_notifications = []

        monitorings = ProductMonitoring.query.filter_by(is_active=True).all()

        for monitoring in monitorings:
            notifications = self.check_and_notify(monitoring)
            all_notifications.extend(notifications)

        return all_notifications

    def _get_best_offer(self, product: Product) -> Offer | None:
        """Obtém a oferta com o melhor preço para um produto"""
        return Offer.query.filter_by(
            product_id=product.id
        ).order_by(Offer.current_price.asc()).first()

    def _get_lowest_historical_price(self, offer: Offer) -> Decimal:
        """Obtém o menor preço já registrado para uma oferta"""
        # Incluir o preço atual
        prices = [offer.current_price]

        # Incluir histórico
        history = PriceHistory.query.filter_by(
            offer_id=offer.id
        ).order_by(PriceHistory.captured_at.asc()).all()

        prices.extend([h.price for h in history])

        return min(prices) if prices else offer.current_price

    def _create_notification(
        self,
        monitoring: ProductMonitoring,
        offer: Offer,
        current_price: Decimal,
        reason: str
    ) -> Notification:
        """Cria uma notificação para o usuário"""

        if reason == "desired_price":
            title = f"Preço alvo atingido! 🎯"
            message = f"{monitoring.product.title} chegou a R${current_price:.2f} na {offer.merchant}!"
        else:  # lowest_price
            title = f"Menor preço registrado! 💰"
            message = f"{monitoring.product.title} com novo menor preço: R${current_price:.2f} na {offer.merchant}!"

        notification = Notification(
            user=monitoring.user,
            product=monitoring.product,
            title=title,
            message=message
        )

        db.session.add(notification)
        return notification

    def get_user_monitorings(self, user: User, active_only: bool = True) -> list[ProductMonitoring]:
        """Obtém os monitoramentos de um usuário"""
        query = ProductMonitoring.query.filter_by(user_id=user.id)

        if active_only:
            query = query.filter_by(is_active=True)

        return query.order_by(ProductMonitoring.created_at.desc()).all()

    def get_user_notifications(self, user: User, limit: int = 50) -> list[Notification]:
        """Obtém as notificações de um usuário"""
        return Notification.query.filter_by(
            user_id=user.id
        ).order_by(Notification.sent_at.desc()).limit(limit).all()
