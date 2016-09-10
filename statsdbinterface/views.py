# -*- coding: utf-8 -*-
from statsdbinterface import server, dbmodels, extmodels
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
        "api_results_per_page": config.API_RESULTS_PER_PAGE,
    })


# The /count/ functions return rows and pages for the lists.

@server.route("/api/count/games")
def api_count_games():
    rowcount = dbmodels.Game.query.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@server.route("/api/count/players")
def api_count_players():
    rowcount = extmodels.Player.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


# Return a list of games.
@server.route("/api/games")
def api_games():
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get a list of games sorted by id and offset by the page.
    games = dbmodels.Game.query.order_by(dbmodels.Game.id).limit(
        config.API_RESULTS_PER_PAGE).offset(
        config.API_RESULTS_PER_PAGE * page).all()

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


# Return a list of players.
@server.route("/api/players")
def api_players():
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get the player list.
    players = extmodels.Player.all(page=page,
        pagesize=config.API_RESULTS_PER_PAGE)

    # Return the list via json.
    ret = []
    for player in players:
        ret.append(player.to_dict())
    resp = jsonify({"players": ret})
    return resp


# Return a single player.
@server.route("/api/players/<string:handle>")
def api_player(handle):
    player = extmodels.Player.get_or_404(handle)
    resp = jsonify(player.to_dict())
    return resp


# Return a single player's games.
@server.route("/api/player:games/<string:handle>")
def api_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    resp = jsonify({"games": player.games()})
    return resp
