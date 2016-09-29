# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, send_from_directory


# displays blueprint
bp = Blueprint(__name__, __name__)


# .
@bp.errorhandler(404)
def not_found(error=None):
    return "404 Not Found", 404


@bp.route('/static/<path:path>')
def static(path):
    return send_from_directory('static', path)


@bp.route("/")
def display_dashboard():
    return render_template('displays/dashboard.html')
