"""
Views representam a camada de apresentacao da aplicacao.
Responsaveis por definir rotas e retornar respostas HTTP ao cliente.
"""
from price.views.main import bp_main

def init_app(app):
    """
    Registra o blueprint na aplicacao Flask e envia mensagem de inicializacao.
    """
    app.register_blueprint(bp_main)
    app.logger.info("Blueprint 'site' registrado com sucesso")