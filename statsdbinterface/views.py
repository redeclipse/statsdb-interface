# -*- coding: utf-8 -*-
from statsdbinterface import server, dbmodels
from flask import jsonify, request
import config
import math


# Return a simple Not Found message upon 404.
@server.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found',
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


# Return configuration information.
@server.route("/api/config")
def api_config():
    return jsonify({
        "results_per_page": config.RESULTS_PER_PAGE,
    })


# The /count/ functions return rows and pages for the lists.

@server.route("/api/count/games")
def api_count_games():
    rowcount = dbmodels.Game.query.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.RESULTS_PER_PAGE),
    })


# Return a list of games.
@server.route("/api/games")
def api_games():
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get a list of games sorted by id and offset by the page.
    games = sorted(dbmodels.Game.query.limit(
                config.RESULTS_PER_PAGE).offset(
                    config.RESULTS_PER_PAGE * page).all(), key=lambda g: g.id)

    # Return the list via json.
    ret = []
    for game in games:
        ret.append(game.to_dict())
    resp = jsonify({"games": ret})
    return resp


# Return a single game.
@server.route("/api/games/<int:gameid>")
def api_game(gameid):
    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()
    resp = jsonify(game.to_dict())
    return resp
