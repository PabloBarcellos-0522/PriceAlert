from datetime import datetime
from flask import Flask

class PriceScannerService:
    """
    Serviço encapsulado em classe responsável por gerenciar a varredura 
    semanal rígida de preços focado na economia de chamadas de API.
    """
    def __init__(self, app: Flask):
        self.app = app

    def scan_all_active_prices(self) -> None:
        """
        Executa a varredura semanal apenas nos produtos monitorados ativamente,
        gera notificações e envia e-mails em lote.
        """
        with self.app.app_context():
            self.app.logger.info("📅 [PriceScannerService] Iniciando varredura semanal de rotina...")
            
            from price.ext.db import db
            from price.models.product import Product
            from price.models.product_monitoring import ProductMonitoring

            try:
                # Query otimizada: busca apenas produtos com monitoramentos ativos
                products_to_scan = db.session.query(Product).join(
                    ProductMonitoring, Product.id == ProductMonitoring.product_id
                ).filter(ProductMonitoring.is_active == True).distinct().all()

                total_products = len(products_to_scan)
                if not products_to_scan:
                    self.app.logger.info("📅 [PriceScannerService] Nenhum produto ativo encontrado para escanear.")
                    return

                self.app.logger.info(f"🔄 [PriceScannerService] Atualizando {total_products} produtos via SerpAPI...")

                calls_made = 0
                for product in products_to_scan:
                    try:
                        if product.product_token:
                            # Utiliza os serviços atrelados ao app de forma limpa
                            self.app.product_service.get_product_details(
                                page_token=product.product_token,
                                commit=False
                            )
                            product.updated_at = datetime.utcnow()
                            calls_made += 1
                        else:
                            self.app.logger.warning(f"⚠️ [PriceScannerService] Produto ID {product.id} não possui product_token.")
                    except Exception as e:
                        self.app.logger.error(f"❌ [PriceScannerService] Erro ao atualizar produto {product.id}: {str(e)}")

                # Salva todas as alterações no banco de uma só vez
                db.session.commit()
                self.app.logger.info(f"✅ [PriceScannerService] {calls_made}/{total_products} consultas realizadas.")

                # Verifica regras de preço e gera notificações
                notifications = self.app.monitoring_service.check_all_active_monitorings()
                self.app.logger.info(f"📬 [PriceScannerService] {len(notifications)} notificações geradas.")

                # Dispara os e-mails em bloco
                if notifications:
                    results = self.app.email_service.send_notifications_batch(notifications)
                    self.app.logger.info(
                        f"📧 [PriceScannerService] Emails enviados: {results.get('sent', 0)}, Falhas: {results.get('failed', 0)}"
                    )

            except Exception as e:
                db.session.rollback()
                self.app.logger.error(f"💥 [PriceScannerService] Falha crítica na rotina de escaneamento: {str(e)}")