from datetime import datetime
from flask import Flask, current_app
from price.ext.db import db
from price.models.product import Product
from price.models.product_monitoring import ProductMonitoring


class PriceScannerService:
    """
    Serviço encapsulado em classe responsável por gerenciar a varredura 
    semanal rígida de preços focado na economia de chamadas de API.
    """

    def scan_all_active_prices(self) -> None:
        """
        Executa a varredura semanal apenas nos produtos monitorados ativamente,
        gera notificações e envia e-mails em lote.
        """
        with current_app.app_context():
            current_app.logger.info(
                "[PriceScannerService] Iniciando varredura semanal de rotina...")

            try:
                # Query otimizada: busca apenas produtos com monitoramentos ativos
                products_to_scan = db.session.query(Product).join(
                    ProductMonitoring, Product.id == ProductMonitoring.product_id
                ).filter(ProductMonitoring.is_active == True).distinct().all()

                total_products = len(products_to_scan)
                if not products_to_scan:
                    current_app.logger.warning(
                        "[PriceScannerService] Nenhum produto ativo encontrado para escanear.")
                    return

                current_app.logger.info(
                    f"[PriceScannerService] Atualizando {total_products} produtos via SerpAPI...")

                calls_made = 0
                for product in products_to_scan:
                    try:
                        if product.product_token:
                            # Utiliza os serviços atrelados ao app de forma limpa
                            current_app.product_service.get_product_details(
                                page_token=product.product_token,
                                commit=False
                            )
                            calls_made += 1
                        else:
                            current_app.logger.warning(
                                f"[PriceScannerService] Produto ID {product.id} não possui product_token.")
                    except Exception as e:
                        current_app.logger.error(
                            f"[PriceScannerService] Erro ao atualizar produto {product.id}: {str(e)}")

                # Salva todas as alterações no banco de uma só vez
                db.session.commit()
                current_app.logger.info(
                    f"[PriceScannerService] {calls_made}/{total_products} consultas realizadas.")

                # Verifica regras de preço e gera notificações
                notifications = current_app.monitoring_service.check_all_active_monitorings()
                current_app.logger.info(
                    f"[PriceScannerService] {len(notifications)} notificações geradas.")

                # Dispara os e-mails em bloco
                if notifications:
                    results = current_app.email_service.send_notifications_batch(
                        notifications)
                    current_app.logger.info(
                        f"[PriceScannerService] Emails enviados: {results.get('sent', 0)}, Falhas: {results.get('failed', 0)}"
                    )

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"[PriceScannerService] Falha crítica na rotina de escaneamento: {str(e)}")

    def update_single_product(self, product_id: int):
        """Atualiza preço de um produto específico"""
        try:
            product = db.session.get(Product, product_id)

            if not product:
                current_app.logger.warning(
                    f"[PriceScannerService] Produto {product_id} não encontrado para escanear.")
                return {"success": False, "error": "Produto não encontrado"}

            current_app.product_service.get_product_details(
                page_token=product.product_token, commit=False)
            db.session.commit()

            current_app.logger.info(
                f"[PriceScannerService] Produto {product.title} atualizado.")
            return {"success": True, "product_id": product_id}

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"[PriceScannerService] Falha crítica na rotina de escaneamento: {str(e)}")
            return {"success": False, "error": str(e)}
