from flask import current_app
from sqlalchemy.engine.url import (
    make_url
)

import click


def ensure_safe_drop_environment():

    app_env = current_app.config.get(
        "APP_ENV"
    )

    if app_env != "development":

        raise click.ClickException(
            "Somente DEV."
        )

    if not current_app.config.get(
        "ALLOW_DROP"
    ):

        raise click.ClickException(
            "ALLOW_DROP desabilitado"
        )


def ensure_safe_seed_environment():

    app_env = current_app.config.get(
        "APP_ENV"
    )

    if app_env != "development":

        raise click.ClickException(
            "Somente DEV."
        )

    if not current_app.config.get(
        "ALLOW_SEED"
    ):

        raise click.ClickException(
            "ALLOW_SEED desabilitado"
        )
