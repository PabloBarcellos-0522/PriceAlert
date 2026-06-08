from flask_wtf import CSRFProtect

csrf = CSRFProtect()


def init_wtf(app):
    if not app.config.get("TESTING"):
        csrf.init_app(app)
