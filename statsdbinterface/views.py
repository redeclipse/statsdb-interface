# -*- coding: utf-8 -*-

import math
from flask import jsonify, request
from werkzeug.exceptions import NotFound
from . import app, dbmodels, extmodels
import config


# Return a simple Not Found message upon 404.
@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found',
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp


@app.route("/api/config")
def api_config():
    """
    Return configuration information.
    """

    return jsonify({
        "api_results_per_page": config.API_RESULTS_PER_PAGE,
        "api_highscore_results": config.API_HIGHSCORE_RESULTS,
    })


@app.route("/api/count/games")
def api_count_games():
    """
    The /count/ functions return rows and pages for the lists.
    """

    rowcount = dbmodels.Game.query.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/players")
def api_count_players():
    rowcount = extmodels.Player.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/player:games/<string:handle>")
def api_count_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    rowcount = len(player.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/servers")
def api_count_servers():
    rowcount = extmodels.Server.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/server:games/<string:handle>")
def api_count_server_games(handle):
    server = extmodels.Server.get_or_404(handle)
    rowcount = len(server.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/maps")
def api_count_maps():
    rowcount = extmodels.Map.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/count/map:games/<string:name>")
def api_count_map_games(name):
    map_ = extmodels.Map.get_or_404(name)
    rowcount = len(map_.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(rowcount / config.API_RESULTS_PER_PAGE),
    })


@app.route("/api/games")
def api_games():
    """
    Return a list of games.
    """

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


@app.route("/api/games/<int:gameid>")
def api_game(gameid):
    """
    Return a single game.
    """

    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()
    resp = jsonify(game.to_dict())
    return resp


@app.route("/api/game:weapons/<int:gameid>")
def api_game_weapons(gameid):
    """
    Return a single games's weapons.
    """

    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()

    ret = {}
    weapons = game.full_weapons()
    for w in weapons:
        ret[w] = weapons[w].to_dict()

    resp = jsonify(ret)

    return resp


@app.route("/api/players")
def api_players():
    """
    Return a list of players.
    """

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


@app.route("/api/players/<string:handle>")
def api_player(handle):
    """
    Return a single player.
    """

    player = extmodels.Player.get_or_404(handle)
    resp = jsonify(player.to_dict())
    return resp


@app.route("/api/player:games/<string:handle>")
def api_player_games(handle):
    """
    Return a single player's games.
    """

    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    player = extmodels.Player.get_or_404(handle)

    resp = jsonify(games=[
        g.to_dict() for g in player.games(
            page=page, pagesize=config.API_RESULTS_PER_PAGE
        )
    ])

    return resp


@app.route("/api/player:weapons/<string:handle>")
def api_player_weapons(handle):
    """
    Return a single player's weapons.
    """

    player = extmodels.Player.get_or_404(handle)

    ret = {}
    weapons = player.weapons()
    for w in weapons:
        ret[w] = weapons[w].to_dict()

    resp = jsonify(ret)

    return resp


@app.route("/api/player:game:weapons/<string:handle>/<int:gameid>")
def api_game_player_weapons(handle, gameid):
    """
    Return a single game player's weapons.
    """

    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()

    if handle not in [p.handle for p in game.players]:
        raise NotFound

    ret = {}
    for weapon in extmodels.Weapon.weapon_list():
        ret[weapon] = extmodels.Weapon.from_game_player(
            weapon, gameid, handle).to_dict()

    resp = jsonify(ret)
    return resp


@app.route(
    "/api/player:game:weapons/<string:handle>/<int:gameid>/<string:weapon>")
def api_game_player_weapon(handle, gameid, weapon):
    """
    Return a single game player's weapons.
    """

    game = dbmodels.Game.query.filter_by(id=gameid).first_or_404()

    if handle not in [p.handle for p in game.players]:
        raise NotFound

    if weapon not in extmodels.Weapon.weapon_list():
        raise NotFound

    resp = jsonify(
        extmodels.Weapon.from_game_player(weapon, gameid, handle).to_dict())
    return resp


@app.route("/api/servers")
def api_servers():
    """
    Return a list of servers.
    """

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


@app.route("/api/servers/<string:handle>")
def api_server(handle):
    """
    Return a single server.
    """

    server = extmodels.Server.get_or_404(handle)
    resp = jsonify(server.to_dict())

    return resp


@app.route("/api/server:games/<string:handle>")
def api_server_games(handle):
    """
    Return a single server's games.
    """

    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    server = extmodels.Server.get_or_404(handle)

    resp = jsonify(games=[
        g.to_dict() for g in
        server.games(page=page, pagesize=config.API_RESULTS_PER_PAGE)
    ])

    return resp


@app.route("/api/maps")
def api_maps():
    """
    Return a list of maps.
    """

    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    # Get the player list.
    maps = extmodels.Map.all(page=page, pagesize=config.API_RESULTS_PER_PAGE)

    # Return the list via json.
    ret = []

    for map_ in maps:
        ret.append(map_.to_dict())

    resp = jsonify({"maps": ret})

    return resp


@app.route("/api/maps/<string:name>")
def api_map(name):
    """
    Return a single map.
    """

    map_ = extmodels.Map.get_or_404(name)
    resp = jsonify(map_.to_dict())
    return resp


@app.route("/api/map:games/<string:name>")
def api_map_games(name):
    """
    Return a single map's games.
    """

    # Get the page number.
    page = request.args.get("page", default=0, type=int)

    map_ = extmodels.Map.get_or_404(name)

    resp = jsonify(
        {
            "games": [g.to_dict() for g in map_.games(
                page=page, pagesize=config.API_RESULTS_PER_PAGE
            )]
        }
    )

    return resp


@app.route("/api/weapons")
def api_weapons():
    ret = {}
    for weapon in extmodels.Weapon.all():
        ret[weapon.name] = weapon.to_dict()
    resp = jsonify(ret)
    return resp


@app.route("/api/weapons/<string:name>")
def api_weapon(name):
    weapon = extmodels.Weapon.get_or_404(name)
    resp = jsonify(weapon.to_dict())
    return resp
