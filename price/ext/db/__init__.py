import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    # 1. Use o driver moderno 'postgresql+psycopg' e force o SSL obrigatório da nuvem
    # Exemplo de URL: postgresql+psycopg://user:pass@ep-instancia.region.neon.tech/neondb?sslmode=require
    DATABASE_URL = os.getenv("DATABASE_URL")

    # If database URL is sqlite, we shouldn't force sslmode=require
    if DATABASE_URL and "sqlite" not in DATABASE_URL:
        if "sslmode=" not in DATABASE_URL:
            DATABASE_URL += "?sslmode=require"

    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if DATABASE_URL and "sqlite" not in DATABASE_URL:
        engine_options["pool_size"] = 5
        engine_options["max_overflow"] = 10

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    db.init_app(app)


def register_models():
    import price.models.user
    import price.models.offer
    import price.models.product
    import price.models.price_history
    import price.models.product_monitoring
    import price.models.notification
