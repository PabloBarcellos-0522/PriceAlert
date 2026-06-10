from datetime import datetime
from flask import Flask

def run_weekly_price_scanner(app: Flask):
    """
    Lógica isolada de escaneamento semanal.
    Varre apenas produtos ativamente monitorados uma única vez.
    """
    # Abre o contexto do app para permitir o uso do banco e dos serviços na thread secundária
    with app.app_context():
        app.logger.info("📅 [Scanner Semanal] Iniciando verificação de rotina...")
        
        # Imports tardios dentro do contexto para evitar erros de importação circular
        from price.ext.db import db
        from price.models.product import Product
        from price.models.product_monitoring import ProductMonitoring

        try:
            # Query que busca apenas produtos com monitoramentos ativos pelos usuários
            products_to_scan = db.session.query(Product).join(
                ProductMonitoring, Product.id == ProductMonitoring.product_id
            ).filter(ProductMonitoring.is_active == True).distinct().all()

            total_products = len(products_to_scan)
            if not products_to_scan:
                app.logger.info("📅 [Scanner Semanal] Nenhum produto ativo para escanear.")
                return

            app.logger.info(f"🔄 [Scanner Semanal] Atualizando {total_products} produtos via SerpAPI...")

            calls_made = 0
            for product in products_to_scan:
                try:
                    if product.product_token:
                        # Faz 1 chamada focada utilizando o token direto do produto
                        app.product_service.get_product_details(
                            page_token=product.product_token,
                            commit=False  # Segura o commit para enviar em lote no final
                        )
                        product.updated_at = datetime.utcnow()
                        calls_made += 1
                    else:
                        app.logger.warning(f"⚠️ [Scanner Semanal] Produto ID {product.id} não possui product_token.")
                except Exception as e:
                    app.logger.error(f"❌ [Scanner Semanal] Erro ao atualizar produto {product.id}: {str(e)}")

            # Commita todas as atualizações de preço e datas de uma só vez
            db.session.commit()
            app.logger.info(f"✅ [Scanner Semanal] {calls_made}/{total_products} consultas realizadas.")

            # Dispara o processamento de notificações com base nos novos preços
            notifications = app.monitoring_service.check_all_active_monitorings()
            app.logger.info(f"📬 [Scanner Semanal] {len(notifications)} notificações geradas.")

            # Envia os e-mails para os usuários em lote
            if notifications:
                results = app.email_service.send_notifications_batch(notifications)
                app.logger.info(
                    f"📧 [Scanner Semanal] Emails enviados: {results.get('sent', 0)}, Falhas: {results.get('failed', 0)}"
                )

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"💥 [Scanner Semanal] Falha crítica na rotina: {str(e)}")