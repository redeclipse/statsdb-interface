# -*- coding: utf-8 -*-

from flask import Flask


app = Flask(__name__)

# Load the rest of the program.
from . import database  # noqa

# Load the database.
database.setup_db(app)
