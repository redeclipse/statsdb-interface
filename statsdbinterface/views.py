# -*- coding: utf-8 -*-
from statsdbinterface import server, dbmodels
from flask import jsonify


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


@server.route("/api/games")
def api_games():
    # Get a list of games sorted by id.
    games = sorted(dbmodels.Game.query.all(), key=lambda g: g.id)
    ret = []
    for game in games:
        ret.append(game.to_dict())
    resp = jsonify({"games": ret})
    return resp


@server.route("/api/games/<int:gameid>")
def api_game(gameid):
    # Get a single game.
    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()
    resp = jsonify(game.to_dict())
    return resp
