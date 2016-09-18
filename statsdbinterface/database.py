# -*- coding: utf-8 -*-
import inspect
import traceback
from flask_sqlalchemy import SQLAlchemy
import config

db_functions = []


# Use as decorator, append f to db_functions.
def db_function(name):
    def d(f):
        def w(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                traceback.print_exc()
                raise
        db_functions.append((name, len(inspect.getargspec(f)[0]), w))
        return f
    return d


db = SQLAlchemy()


# Create database connection and import models.
def setup_db(server):
    # initialize Flask-SQLAlchemy following app factory pattern
    # http://flask.pocoo.org/docs/0.11/patterns/appfactories/
    db.init_app(server)

    # Set the SQLAlchemy Database URI from the config.
    server.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///%s/stats.sqlite' % (config.data_directory.rstrip('/')))

    # Create the SQLAlchemy connection.

    @db.event.listens_for(db.engine, 'begin')
    def register_functions(conn):
        for f in db_functions:
            conn.connection.create_function(f[0], f[1], f[2])

    # Register models, functions and views.
    from statsdbinterface import redeclipse, dbmodels, views
