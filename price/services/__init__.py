from flask import Flask
from flask_mail import Mail
from price.services.email_service import EmailService
from price.services.monitoring_service import MonitoringService
from price.services.product_service import SerpapiProductService
from price.services.serpapi_service import SerpApiService


def init_services(app: Flask) -> None:
    mail = Mail(app)

    app.mail = mail
    app.email_service = EmailService(mail)
    app.serpapi_service = SerpApiService()
    app.product_service = SerpapiProductService(app.serpapi_service)
    app.monitoring_service = MonitoringService()

    app.logger.info("Serviços registrados com sucesso")
