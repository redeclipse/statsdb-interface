import math
from flask import jsonify, request, Blueprint, current_app
from werkzeug.exceptions import NotFound
from ..database import models, extmodels


# api blueprint
bp = Blueprint(__name__, __name__, url_prefix='/api')


@bp.route("/config")
def api_config():
    """
    Return configuration information.
    """

    return jsonify({
        "api_results_per_page": current_app.config['API_RESULTS_PER_PAGE'],
        "api_highscore_results": current_app.config['API_HIGHSCORE_RESULTS'],
        "display_results_per_page":
            current_app.config['DISPLAY_RESULTS_PER_PAGE'],
        "display_results_recent": current_app.config['DISPLAY_RESULTS_RECENT'],
    })


@bp.route("/count/games")
def api_count_games():
    """
    The /count/ functions return rows and pages for the lists.
    """

    rowcount = models.Game.query.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/players")
def api_count_players():
    rowcount = extmodels.Player.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/player:games/<string:handle>")
def api_count_player_games(handle):
    player = extmodels.Player.get_or_404(handle)
    rowcount = len(player.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/servers")
def api_count_servers():
    rowcount = extmodels.Server.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/server:games/<string:handle>")
def api_count_server_games(handle):
    server = extmodels.Server.get_or_404(handle)
    rowcount = len(server.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/maps")
def api_count_maps():
    rowcount = extmodels.Map.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/map:games/<string:name>")
def api_count_map_games(name):
    map_ = extmodels.Map.get_or_404(name)
    rowcount = len(map_.game_ids)
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/games")
def api_games():
    """
    Return a list of games.
    """

    # Get a list of games sorted by id and offset by the page.
    games = models.Game.query.order_by(models.Game.id).paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['API_RESULTS_PER_PAGE']).items

    # Return the list via json.
    ret = []
    for game in games:
        ret.append(game.to_dict())
    resp = jsonify({"games": ret})
    return resp


@bp.route("/api/games/<int:gameid>")
def api_game(gameid):
    """
    Return a single game.
    """

    game = models.Game.query.filter_by(id=gameid).first_or_404()
    resp = jsonify(game.to_dict())
    return resp


@bp.route("/game:weapons/<int:gameid>")
def api_game_weapons(gameid):
    """
    Return a single games's weapons.
    """

    game = models.Game.query.filter_by(id=gameid).first_or_404()

    ret = {}
    weapons = game.full_weapons()
    for w in weapons:
        ret[w] = weapons[w].to_dict()

    resp = jsonify(ret)

    return resp


@bp.route("/players")
def api_players():
    """
    Return a list of players.
    """

    # Get the player list.
    players = extmodels.Player.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['API_RESULTS_PER_PAGE']).items

    # Return the list via json.
    ret = []
    for player in players:
        ret.append(player.to_dict())
    resp = jsonify({"players": ret})
    return resp


@bp.route("/players/<string:handle>")
def api_player(handle):
    """
    Return a single player.
    """

    player = extmodels.Player.get_or_404(handle)
    resp = jsonify(player.to_dict())
    return resp


@bp.route("/player:games/<string:handle>")
def api_player_games(handle):
    """
    Return a single player's games.
    """

    player = extmodels.Player.get_or_404(handle)

    resp = jsonify(games=[
        g.to_dict() for g in player.games_paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['API_RESULTS_PER_PAGE']).items
    ])

    return resp


@bp.route("/player:weapons/<string:handle>")
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


@bp.route("/player:game:weapons/<string:handle>/<int:gameid>")
def api_game_player_weapons(handle, gameid):
    """
    Return a single game player's weapons.
    """

    game = models.Game.query.filter_by(id=gameid).first_or_404()

    if handle not in [p.handle for p in game.players]:
        raise NotFound

    ret = {}
    for weapon in extmodels.Weapon.weapon_list():
        ret[weapon] = extmodels.Weapon.from_game_player(
            weapon, gameid, handle).to_dict()

    resp = jsonify(ret)
    return resp


@bp.route(
    "/player:game:weapons/<string:handle>/<int:gameid>/<string:weapon>")
def api_game_player_weapon(handle, gameid, weapon):
    """
    Return a single game player's weapons.
    """

    game = models.Game.query.filter_by(id=gameid).first_or_404()

    if handle not in [p.handle for p in game.players]:
        raise NotFound

    if weapon not in extmodels.Weapon.weapon_list():
        raise NotFound

    resp = jsonify(
        extmodels.Weapon.from_game_player(weapon, gameid, handle).to_dict())
    return resp


@bp.route("/servers")
def api_servers():
    """
    Return a list of servers.
    """

    # Get the server list.
    servers = extmodels.Server.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['API_RESULTS_PER_PAGE']).items

    # Return the list via json.
    ret = []

    for server in servers:
        ret.append(server.to_dict())

    resp = jsonify({"servers": ret})

    return resp


@bp.route("/servers/<string:handle>")
def api_server(handle):
    """
    Return a single server.
    """

    server = extmodels.Server.get_or_404(handle)
    resp = jsonify(server.to_dict())

    return resp


@bp.route("/server:games/<string:handle>")
def api_server_games(handle):
    """
    Return a single server's games.
    """

    server = extmodels.Server.get_or_404(handle)

    resp = jsonify(games=[
        g.to_dict() for g in
        server.games_paginate(
            request.args.get("page", default=1, type=int),
            current_app.config['API_RESULTS_PER_PAGE']).items
    ])

    return resp


@bp.route("/maps")
def api_maps():
    """
    Return a list of maps.
    """

    # Get the map list.
    maps = extmodels.Map.paginate(
        request.args.get("page", default=1, type=int),
        current_app.config['API_RESULTS_PER_PAGE']).items

    # Return the list via json.
    ret = []

    for map_ in maps:
        ret.append(map_.to_dict())

    resp = jsonify({"maps": ret})

    return resp


@bp.route("/maps/<string:name>")
def api_map(name):
    """
    Return a single map.
    """

    map_ = extmodels.Map.get_or_404(name)
    resp = jsonify(map_.to_dict())
    return resp


@bp.route("/map:games/<string:name>")
def api_map_games(name):
    """
    Return a single map's games.
    """

    map_ = extmodels.Map.get_or_404(name)

    resp = jsonify(
        {
            "games": [g.to_dict() for g in map_.games_paginate(
                request.args.get("page", default=1, type=int),
                current_app.config['API_RESULTS_PER_PAGE']).items
            ]
        }
    )

    return resp


@bp.route("/weapons")
def api_weapons():
    ret = {}
    for weapon in extmodels.Weapon.all():
        ret[weapon.name] = weapon.to_dict()
    resp = jsonify(ret)
    return resp


@bp.route("/weapons/<string:name>")
def api_weapon(name):
    weapon = extmodels.Weapon.get_or_404(name)
    resp = jsonify(weapon.to_dict())
    return resp


@bp.route("/modes")
def api_modes():
    ret = {}
    for mode in extmodels.Mode.all():
        ret[mode.name] = mode.to_dict()
    return jsonify(ret)


@bp.route("/modes/<string:name>")
def api_mode(name):
    mode = extmodels.Mode.get_or_404(name)
    return jsonify(mode.to_dict())


@bp.route("/mutators")
def api_mutators():
    ret = {}
    for mutator in extmodels.Mutator.all():
        ret[mutator.name] = mutator.to_dict()
    return jsonify(ret)


@bp.route("/mutators/<string:name>")
def api_mutator(name):
    mutator = extmodels.Mutator.get_or_404(name)
    return jsonify(mutator.to_dict())
