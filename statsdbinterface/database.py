# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
import config


# Create database connection and import models.
def load(server):
    # The database is used elsewhere.
    global db

    # Set the SQLAlchemy Database URI from the config.
    server.config['SQLALCHEMY_DATABASE_URI'] = (
        'sqlite:///%s/stats.sqlite' % (config.data_directory.rstrip('/')))

    # Load the database.
    db = SQLAlchemy(server)

    # Register models and views.
    from statsdbinterface import dbmodels, views
