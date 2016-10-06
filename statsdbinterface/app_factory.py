from flask import Flask
from . import defaults


def create_app(data_dir):
    """
    Implementation of the app factory pattern.

    http://flask.pocoo.org/docs/patterns/appfactories/

    :return: A Flask WSGI app object
    :rtype: `flask.Flask`
    """

    app = Flask(__name__)
    app.config.from_object(defaults)
    try:
        import config
        app.config.from_object(config)
    except ImportError:
        # No config.py, just use the defaults.
        pass

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///%s/stats.sqlite' % (data_dir.rstrip('/')))

    # Load the rest of the program.
    from .database.core import setup_db

    # Load the database.
    setup_db(app)

    # Register views
    from .views import api, displays
    app.register_blueprint(api.bp)
    app.register_blueprint(displays.bp)

    # set up error handling
    from .error_handling import setup_app
    setup_app(app)

    # Begin cache cleaner.
    from . import function_cache
    function_cache.setup()

    return app
