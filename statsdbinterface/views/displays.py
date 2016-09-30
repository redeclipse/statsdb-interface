# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, send_from_directory, request
from .. import dbmodels
from .utils import Pages
import config


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


@bp.route("/games")
def display_games():
    page = request.args.get("page", default=0, type=int)
    pages = Pages(page, config.DISPLAY_RESULTS_PER_PAGE,
                  dbmodels.Game.query.count())

    games = dbmodels.Game.query.order_by(dbmodels.Game.id.desc()).limit(
        pages.size).offset(
        pages.size * page).all()

    return render_template('displays/games.html', games=games, pages=pages)


@bp.route("/games/<int:gameid>")
def display_game(gameid):
    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()
    return render_template('displays/game.html', game=game)
