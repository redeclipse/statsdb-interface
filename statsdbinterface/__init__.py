# -*- coding: utf-8 -*-

from flask import Flask, request


def create_app(config):
    """
    Implementation of the app factory pattern.

    http://flask.pocoo.org/docs/patterns/appfactories/

    :return: A Flask WSGI app object
    :rtype: `flask.Flask`
    """

    app = Flask(__name__)
    app.config.from_object(config)

    # Load the rest of the program.
    from . import database  # noqa

    # Load the database.
    database.setup_db(app)

    # Register views
    from .views import api, displays
    app.register_blueprint(api.bp)
    app.register_blueprint(displays.bp)

    # Dispatch error handlers correctly.
    @app.errorhandler(404)
    def not_found(error=None):
        if request.path.lstrip("/").split("/")[0] == "api":
            return api.not_found(error)
        else:
            return displays.not_found(error)

    @app.errorhandler(500)
    def internal_error(error=None):
        if request.path.lstrip("/").split("/")[0] == "api":
            return api.internal_error(error)
        else:
            return displays.internal_error(error)

    return app
