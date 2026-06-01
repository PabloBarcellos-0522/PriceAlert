import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    # 1. Use o driver moderno 'postgresql+psycopg' e force o SSL obrigatório da nuvem
    # Exemplo de URL: postgresql+psycopg://user:pass@ep-instancia.region.neon.tech/neondb?sslmode=require
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL and "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10
    }

    db.init_app(app)


def register_models():
    import price.models.user
    import price.models.offer
    import price.models.product
    import price.models.price_history
    import price.models.product_monitoring
    import price.models.notification

    pass
    # """
    # Importa todos os modulos que definem modelos para que sejam registrados
    # no metadata do SQLAlchemy antes de operacoes como create_all().
    # """
    # import delivery.models.role
    # import delivery.models.user
    # import delivery.models.level
    # import delivery.models.business
    # import delivery.models.business_owners
    # import delivery.models.business_type
    # import delivery.models.role_user
    # import delivery.models.location
    # import delivery.models.order
