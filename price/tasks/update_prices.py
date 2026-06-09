"""
Tarefa para atualizar preços e enviar notificações

Pode ser executada periodicamente via APScheduler, Celery ou outro job scheduler.

Exemplo com APScheduler:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_all_prices, trigger="interval", hours=1)
    scheduler.start()
"""

from flask import current_app
from price.ext.db import db
from price.models.product import Product


def update_all_prices_and_notify():
    """
    Atualiza preços de todos os produtos monitorados e envia notificações

    Esta é a tarefa principal que deve ser executada periodicamente
    """
    try:
        # Obtém todos os produtos sendo monitorados
        from price.models.product_monitoring import ProductMonitoring

        products_to_update = db.session.query(Product).join(
            ProductMonitoring, Product.id == ProductMonitoring.product_id
        ).filter(ProductMonitoring.is_active == True).distinct().all()

        current_app.logger.info(
            f"Atualizando {len(products_to_update)} produtos...")

        # 1. Atualiza preços
        updated_count = 0
        for product in products_to_update:
            try:
                current_app.product_service.update_product_offers(product)
                updated_count += 1
            except Exception as e:
                current_app.logger.error(
                    f"Erro ao atualizar produto {product.id}: {str(e)}")

        current_app.logger.info(f"✅ {updated_count} produtos atualizados")

        # 2. Verifica monitoramentos e cria notificações
        notifications = current_app.monitoring_service.check_all_active_monitorings()
        current_app.logger.info(f"📬 {len(notifications)} notificações criadas")

        # 3. Envia emails
        if notifications:
            results = current_app.email_service.send_notifications_batch(
                notifications)
            current_app.logger.info(
                f"📧 Emails enviados: {results['sent']}, Falhas: {results['failed']}")

        return {
            "success": True,
            "products_updated": updated_count,
            "notifications_created": len(notifications),
            "timestamp": db.func.now()
        }

    except Exception as e:
        current_app.logger.error(f"❌ Erro na tarefa de atualização: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def update_single_product(product_id: int):
    """Atualiza preço de um produto específico"""
    try:
        product = db.session.query(Product, product_id)

        if not product:
            current_app.logger.warning(f"Produto {product_id} não encontrado")
            return {"success": False, "error": "Produto não encontrado"}

        current_app.product_service.update_product_offers(product)

        current_app.logger.info(f"✅ Produto {product.title} atualizado")
        return {"success": True, "product_id": product_id}

    except Exception as e:
        current_app.logger.error(
            f"Erro ao atualizar produto {product_id}: {str(e)}")
        return {"success": False, "error": str(e)}


def check_and_notify_all():
    """Apenas verifica monitoramentos e envia notificações (sem atualizar preços)"""
    try:
        notifications = current_app.monitoring_service.check_all_active_monitorings()
        current_app.logger.info(
            f"📬 {len(notifications)} notificações verificadas")

        if notifications:
            results = current_app.email_service.send_notifications_batch(
                notifications)
            current_app.logger.info(
                f"📧 Emails enviados: {results['sent']}, Falhas: {results['failed']}")
            return results

        return {"total": 0, "sent": 0, "failed": 0}

    except Exception as e:
        current_app.logger.error(f"Erro ao verificar notificações: {str(e)}")
        raise


def cleanup_old_notifications(days: int = 30):
    """Remove notificações antigas do banco de dados"""
    try:
        from datetime import datetime, timedelta
        from price.models.notification import Notification

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = Notification.query.filter(
            Notification.sent_at < cutoff_date
        ).delete()

        db.session.commit()

        current_app.logger.info(
            f"🗑️  {deleted_count} notificações antigas removidas")
        return {"success": True, "deleted": deleted_count}

    except Exception as e:
        current_app.logger.error(f"Erro ao limpar notificações: {str(e)}")
        db.session.rollback()
        return {"success": False, "error": str(e)}
