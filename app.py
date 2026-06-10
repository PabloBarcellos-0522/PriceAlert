import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask


# ==========================================================
# CARREGAMENTO CENTRALIZADO DE AMBIENTE
# ==========================================================

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    # Configuracao recomendada para desenvolvimento:
    # Mostra mensagens DEBUG e INFO no console
    if app.debug:
        log_file = os.path.join(app.instance_path, 'app.log')
        handler = RotatingFileHandler(
            log_file, maxBytes=100000, backupCount=10)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] - %(levelname)s: %(message)s'))
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)

    # ----------------------------------------------------------
    # Configuracao da aplicacao (variaveis de ambiente)
    # ----------------------------------------------------------
    from price.ext.config import init_config
    init_config(app)

    if test_config:
        app.config.update(test_config)

    # ----------------------------------------------------------
    # Personalizacao do CLI no sistema
    # ----------------------------------------------------------
    from price.ext.cli import init_cli
    init_cli(app)

    # ----------------------------------------------------------
    # Inicializacao do banco de dados
    # ----------------------------------------------------------
    from price.ext.db import init_db
    init_db(app)

    # Registro dos modelos no metadata do SQLAlchemy
    from price.ext.db import register_models
    register_models()

    # ----------------------------------------------------------
    # Outras extensoes
    # ----------------------------------------------------------
    if not app.config.get("TESTING"):
        from price.ext.wtf import init_wtf
        init_wtf(app)

    if app.debug or app.config.get("DEBUG"):
        from price.ext.debugtoolbar import init_toolbar
        init_toolbar(app)

    # ----------------------------------------------------------
    # Blueprints (camada de apresentacao)
    # ----------------------------------------------------------
    from price.views import init_site
    init_site(app)

    # ----------------------------------------------------------
    # Services (camada de negocio)
    # ----------------------------------------------------------
    from price.services import init_services
    init_services(app)

# ----------------------------------------------------------
    # Background Tasks / Scanner Semanal Isolado
    # ----------------------------------------------------------
    from price.tasks import init_tasks
    init_tasks(app)

    return app
