from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def setup_db(app):
    """
    Create database connection and import models.
    """

    # initialize Flask-SQLAlchemy following app factory pattern
    # http://flask.pocoo.org/docs/0.11/patterns/appfactories/
    db.init_app(app)

    # Register models, functions and views.
    from .. import views  # noqa
    from . import models  # noqa

    with app.app_context():
        models.Mode.init()
        models.Mutator.init()
