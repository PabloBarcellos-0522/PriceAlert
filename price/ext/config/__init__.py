import os
from dotenv import load_dotenv


def init_config(app):
    # Carrega variaveis do ambiente (ja selecionado via tasks.py)
    load_dotenv(override=True)

    app.config['APP_ENV'] = os.environ.get('APP_ENV')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1'
    app.config['ALLOW_SEED'] = os.environ.get('ALLOW_SEED') == 'False'
    app.config['ALLOW_DROP'] = os.environ.get('ALLOW_DROP') == 'False'

    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    app.config['SERPAPI_API_KEY'] = os.environ['SERPAPI_API_KEY']

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///instance/pricealert.db'
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if app.debug:
        app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        app.config['DEBUG_TB_PANELS'] = (
            'flask_debugtoolbar.panels.versions.VersionDebugPanel',
            'flask_debugtoolbar.panels.timer.TimerDebugPanel',
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel',
            'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
            # 'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel', <--- REMOVA OU COMENTE ESTA LINHA
        )
