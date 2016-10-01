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

    # set up error handling
    from .error_handling import setup_app
    setup_app(app)

    return app
