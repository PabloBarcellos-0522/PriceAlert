import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
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
