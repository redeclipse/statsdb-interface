# -*- coding: utf-8 -*-
from flask import Flask
server = Flask(__name__)

# Load the rest of the program.
from statsdbinterface import database, views

# Load the database.
database.load()


# Register a function to unload the database upon exit.
@server.teardown_appcontext
def shutdown_session(exception=None):
    database.unload()
