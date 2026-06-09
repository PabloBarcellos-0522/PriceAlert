import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

def init_tasks(app: Flask) -> None:
    """
    Inicializa o agendador de tarefas (APScheduler) e agenda a execução
    do PriceScannerService que já foi previamente registrado no objeto app.
    """
    
    # TRAVAS DE SEGURANÇA CONTRA DESPERDÍCIO DE CRÉDITOS:
    if app.config.get("TESTING") or (app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true"):
        return

    # Recupera o serviço que foi instanciado pelo init_services
    price_scanner_service = getattr(app, 'price_scanner_service', None)
    
    if not price_scanner_service:
        app.logger.error("❌ [Tasks] Não foi possível encontrar o 'price_scanner_service' registrado no app.")
        return

    # Configura e liga o relógio
    scheduler = BackgroundScheduler()
    app.scheduler = scheduler

    # Roda estritamente todo DOMINGO às 03:00 da manhã
    scheduler.add_job(
        func=price_scanner_service.scan_all_active_prices,
        trigger="cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="strict_weekly_price_scanner_job"
    )

    scheduler.start()
    app.logger.info("⏰ [Tasks] Agendador semanal ativado com sucesso usando o serviço centralizado")