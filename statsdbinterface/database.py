# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config


# Create database connection and import models.
def load():
    # The session and base are used elsewhere.
    global db_session
    global Base

    engine = create_engine(
        'sqlite:///%s/stats.sqlite' % (config.data_directory.rstrip('/')),
                           convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base = declarative_base()
    Base.query = db_session.query_property()

    import statsdbinterface.dbmodels

    Base.metadata.create_all(bind=engine)


# Remove the DB session.
def unload():
    global db_session

    db_session.remove()
