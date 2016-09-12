# -*- coding: utf-8 -*-
import math
from flask import jsonify, request
from statsdbinterface import server, dbmodels, extmodels
import config


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
        "api_highscore_results": config.API_HIGHSCORE_RESULTS,
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


@server.route("/api/count/player:games/<string:handle>")
def api_count_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    rowcount = len(player.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@server.route("/api/count/servers")
def api_count_servers():
    rowcount = extmodels.Server.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@server.route("/api/count/server:games/<string:handle>")
def api_count_server_games(handle):
    server = extmodels.Server.get_or_404(handle)
    rowcount = len(server.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@server.route("/api/count/maps")
def api_count_maps():
    rowcount = extmodels.Map.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@server.route("/api/count/map:games/<string:name>")
def api_count_map_games(name):
    map_ = extmodels.Map.get_or_404(name)
    rowcount = len(map_.game_ids)
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
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    player = extmodels.Player.get_or_404(handle)
    resp = jsonify({"games": [g.to_dict() for g in player.games(page=page,
        pagesize=config.API_RESULTS_PER_PAGE)]})
    return resp


# Return a list of servers.
@server.route("/api/servers")
def api_servers():
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get the player list.
    servers = extmodels.Server.all(page=page,
                                   pagesize=config.API_RESULTS_PER_PAGE)

    # Return the list via json.
    ret = []
    for server in servers:
        ret.append(server.to_dict())
    resp = jsonify({"servers": ret})
    return resp


# Return a single server.
@server.route("/api/servers/<string:handle>")
def api_server(handle):
    server = extmodels.Server.get_or_404(handle)
    resp = jsonify(server.to_dict())
    return resp


# Return a single server's games.
@server.route("/api/server:games/<string:handle>")
def api_server_games(handle):
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    server = extmodels.Server.get_or_404(handle)
    resp = jsonify({"games": [g.to_dict() for g in server.games(page=page,
        pagesize=config.API_RESULTS_PER_PAGE)]})
    return resp


# Return a list of maps.
@server.route("/api/maps")
def api_maps():
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get the player list.
    maps = extmodels.Map.all(page=page,
                                   pagesize=config.API_RESULTS_PER_PAGE)

    # Return the list via json.
    ret = []
    for map_ in maps:
        ret.append(map_.to_dict())
    resp = jsonify({"maps": ret})
    return resp


# Return a single map.
@server.route("/api/maps/<string:name>")
def api_map(name):
    map_ = extmodels.Map.get_or_404(name)
    resp = jsonify(map_.to_dict())
    return resp


# Return a single map's games.
@server.route("/api/map:games/<string:name>")
def api_map_games(name):
    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    map_ = extmodels.Map.get_or_404(name)
    resp = jsonify({"games": [g.to_dict() for g in map_.games(page=page,
        pagesize=config.API_RESULTS_PER_PAGE)]})
    return resp
