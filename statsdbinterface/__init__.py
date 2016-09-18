# -*- coding: utf-8 -*-
from flask import Flask
server = Flask(__name__)

# Load the rest of the program.
from statsdbinterface import database

# Load the database.
database.setup_db(server)
