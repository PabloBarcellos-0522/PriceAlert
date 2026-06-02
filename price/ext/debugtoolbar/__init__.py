from flask_debugtoolbar import DebugToolbarExtension

toolbar = DebugToolbarExtension()


def init_toolbar(app):
    toolbar.init_app(app)
