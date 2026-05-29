import os
import logging
from dotenv import load_dotenv
from flask import Flask


# ==========================================================
# CARREGAMENTO CENTRALIZADO DE AMBIENTE
# ==========================================================

# env = os.environ.get("APP_ENV", "dev")

# load_dotenv(f".env.{env}", override=True)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    # Configuracao recomendada para desenvolvimento:
    # Mostra mensagens DEBUG e INFO no console
    if app.debug:
        app.logger.setLevel(logging.DEBUG)

    # ----------------------------------------------------------
    # Configuracao da aplicacao (variaveis de ambiente)
    # ----------------------------------------------------------
    from price.ext.config import init_app as init_config
    init_config(app)

    if test_config:
        app.config.update(test_config)

    # ----------------------------------------------------------
    # Personalizacao do CLI no sistema
    # ----------------------------------------------------------
    from price.ext.cli import init_app as init_cli
    init_cli(app)

    # ----------------------------------------------------------
    # Inicializacao do banco de dados
    # ----------------------------------------------------------
    from price.ext.db import init_app as init_db
    init_db(app)

    # Registro dos modelos no metadata do SQLAlchemy
    from price.ext.db import register_models
    register_models()

    # ----------------------------------------------------------
    # Outras extensoes
    # ----------------------------------------------------------
    if not app.config.get("TESTING"):
        from price.ext.wtf import init_app as init_wtf
        init_wtf(app)

    from price.ext.debugtoolbar import init_app as init_toolbar
    init_toolbar(app)

    # ----------------------------------------------------------
    # Blueprints (camada de apresentacao)
    # ----------------------------------------------------------
    from price.views import init_app as init_site
    init_site(app)

    return app
