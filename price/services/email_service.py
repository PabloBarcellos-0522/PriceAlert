from flask import current_app, render_template_string
from flask_mail import Mail, Message
from price.models.notification import Notification
from price.models.user import User


class EmailService:
    """Serviço de envio de emails para notificações"""

    def __init__(self, mail: Mail = None):
        self.mail = mail

    def send_notification_email(self, notification: Notification) -> bool:
        """Envia email de notificação para o usuário"""
        try:
            msg = Message(
                subject=notification.title,
                recipients=[notification.user.email],
                html=self._render_notification_template(notification),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )

            self.mail.send(msg)
            return True

        except Exception as e:
            current_app.logger.error(f"Erro ao enviar email: {str(e)}")
            return False

    def send_notifications_batch(self, notifications: list[Notification]) -> dict:
        """Envia lote de notificações por email"""
        results = {
            "total": len(notifications),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for notification in notifications:
            try:
                if self.send_notification_email(notification):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "notification_id": notification.id,
                    "user_email": notification.user.email,
                    "error": str(e)
                })

        return results

    def send_daily_digest(self, user: User, notifications: list[Notification]) -> bool:
        """Envia um resumo diário de notificações"""
        if not notifications:
            return True

        try:
            msg = Message(
                subject=f"📊 PriceAlert - Resumo do dia ({len(notifications)} alertas)",
                recipients=[user.email],
                html=self._render_digest_template(user, notifications),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )

            self.mail.send(msg)
            return True

        except Exception as e:
            current_app.logger.error(f"Erro ao enviar digest: {str(e)}")
            return False

    def send_welcome_email(self, user: User) -> bool:
        """Envia email de boas-vindas"""
        try:
            msg = Message(
                subject="Bem-vindo ao PriceAlert! 🎉",
                recipients=[user.email],
                html=self._render_welcome_template(user),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )

            self.mail.send(msg)
            return True

        except Exception as e:
            current_app.logger.error(
                f"Erro ao enviar email de boas-vindas: {str(e)}")
            return False

    def _render_notification_template(self, notification: Notification) -> str:
        """Renderiza template HTML para notificação"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                .content { margin: 20px 0; color: #666; line-height: 1.6; }
                .product-info { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; }
                .footer { color: #999; font-size: 12px; margin-top: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{{ title }}</h2>
                </div>
                <div class="content">
                    <p>Olá {{ user.name }},</p>
                    <div class="product-info">
                        <p><strong>{{ message }}</strong></p>
                        <p>Produto: <strong>{{ product.title }}</strong></p>
                    </div>
                    <p>Continue acompanhando seus produtos favoritos no PriceAlert!</p>
                </div>
                <div class="footer">
                    <p>Este é um email automático do PriceAlert. Não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return render_template_string(
            template,
            title=notification.title,
            message=notification.message,
            product=notification.product,
            user=notification.user
        )

    def _render_digest_template(self, user: User, notifications: list[Notification]) -> str:
        """Renderiza template HTML para digest diário"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                .notification-item { background-color: #f9f9f9; padding: 12px; margin: 10px 0; border-left: 4px solid #007bff; }
                .footer { color: #999; font-size: 12px; margin-top: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 Resumo do dia - {{ notification_count }} alertas</h2>
                </div>
                <div class="content">
                    <p>Olá {{ user.name }},</p>
                    <p>Você recebeu {{ notification_count }} alertas de preço hoje:</p>
                    {% for notification in notifications %}
                    <div class="notification-item">
                        <p><strong>{{ notification.title }}</strong></p>
                        <p>{{ notification.message }}</p>
                        <small>{{ notification.sent_at.strftime('%H:%M') }}</small>
                    </div>
                    {% endfor %}
                </div>
                <div class="footer">
                    <p>Este é um email automático do PriceAlert. Não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return render_template_string(
            template,
            user=user,
            notifications=notifications,
            notification_count=len(notifications)
        )

    def _render_welcome_template(self, user: User) -> str:
        """Renderiza template HTML para email de boas-vindas"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 20px auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                .content { margin: 20px 0; color: #666; line-height: 1.6; }
                .footer { color: #999; font-size: 12px; margin-top: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Bem-vindo ao PriceAlert! 🎉</h2>
                </div>
                <div class="content">
                    <p>Olá {{ user.name }},</p>
                    <p>Obrigado por se cadastrar no PriceAlert! Você agora pode:</p>
                    <ul>
                        <li>Buscar produtos no Google Shopping</li>
                        <li>Monitorar preços em tempo real</li>
                        <li>Receber alertas quando o preço cair</li>
                        <li>Manter histórico de variação de preços</li>
                    </ul>
                    <p>Comece a monitorar seus produtos favoritos agora!</p>
                </div>
                <div class="footer">
                    <p>Este é um email automático do PriceAlert. Não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return render_template_string(template, user=user)
