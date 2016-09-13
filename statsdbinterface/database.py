# -*- coding: utf-8 -*-
import inspect
from flask_sqlalchemy import SQLAlchemy
import config

db_functions = []


# Use as decorator, append f to db_functions.
def db_function(name):
    def d(f):
        db_functions.append((name, len(inspect.getargspec(f)[0]), f))
        return f
    return d


# Create database connection and import models.
def load(server):
    # The database is used elsewhere.
    global db

    # Set the SQLAlchemy Database URI from the config.
    server.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///%s/stats.sqlite' % (config.data_directory.rstrip('/')))

    # Create the SQLAlchemy connection.
    db = SQLAlchemy(server)

    @db.event.listens_for(db.engine, 'begin')
    def register_functions(conn):
        for f in db_functions:
            conn.connection.create_function(f[0], f[1], f[2])

    # Register models, functions and views.
    from statsdbinterface import redeclipse, dbmodels, views
