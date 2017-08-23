import math
from collections import OrderedDict
from flask import jsonify, request, Blueprint, current_app
from werkzeug.exceptions import NotFound
from ..database.core import db
from ..database.models import Game, GamePlayer, GameServer, GameWeapon, \
    Mutator, Mode, GameMutator
from ..utils import page, result_to_dict, raise404
from .. import rankings


def game_ids(q, name_key):
    items = OrderedDict()
    for name, gid in q:
        items.setdefault(name, {name_key: name, 'game_ids': []})
        items[name]['game_ids'].append(gid)
    return items


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
        "display_highscore_results": current_app.config['DISPLAY_HIGHSCORE_RESULTS'],
        "display_results_per_page": current_app.config['DISPLAY_RESULTS_PER_PAGE'],
        "display_results_recent": current_app.config['DISPLAY_RESULTS_RECENT'],
    })


@bp.route("/count/games")
def api_count_games():
    """
    The /count/ functions return rows and pages for the lists.
    """
    rowcount = Game.query.count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/players")
def api_count_players():
    rowcount = db.session \
        .query(db.distinct(GamePlayer.handle)) \
        .filter(GamePlayer.handle.isnot(None)) \
        .count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/player:games/<string:handle>")
def api_count_player_games(handle):
    rowcount = GamePlayer.query.filter_by(handle=handle).count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/servers")
def api_count_servers():
    rowcount = db.session \
        .query(db.distinct(GameServer.handle)) \
        .count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/server:games/<string:handle>")
def api_count_server_games(handle):
    rowcount = GameServer.query \
        .filter_by(handle=handle) \
        .count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/maps")
def api_count_maps():
    rowcount = db.session \
        .query(db.distinct(Game.map)) \
        .count()
    return jsonify({
        "rows": rowcount,
        "pages": math.ceil(
            rowcount / current_app.config['API_RESULTS_PER_PAGE']),
    })


@bp.route("/count/map:games/<string:name>")
def api_count_map_games(name):
    rowcount = Game.query \
        .filter_by(map=name) \
        .count()
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
    games_q = Game.query \
        .options(db.joinedload(Game.players)) \
        .options(db.joinedload(Game.teams)) \
        .options(db.joinedload(Game.ffarounds)) \
        .options(db.joinedload(Game.captures)) \
        .options(db.joinedload(Game.bombings)) \
        .order_by(Game.id.desc())
    games_q = page(games_q)
    return jsonify({"games": [g.to_dict() for g in games_q]})


@bp.route("/games/<int:gameid>")
def api_game(gameid):
    """
    Return a single game.
    """
    game = Game.query.get_or_404(gameid)
    return jsonify(game.to_dict())


@bp.route("/game:weapons/<int:gameid>")
def api_game_weapons(gameid):
    """
    Return a single games's weapons.
    """
    weapons_q = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.flakhits1).label('flakhits1'),
            db.func.sum(GameWeapon.flakhits2).label('flakhits2'),
            db.func.sum(GameWeapon.flakshots1).label('flakshots1'),
            db.func.sum(GameWeapon.flakshots2).label('flakshots2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2'),
            db.func.sum(GameWeapon.hits1).label('hits1'),
            db.func.sum(GameWeapon.hits2).label('hits2'),
            db.func.sum(GameWeapon.shots1).label('shots1'),
            db.func.sum(GameWeapon.shots2).label('shots2'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded')) \
        .filter(GameWeapon.game_id == gameid) \
        .group_by(GameWeapon.weapon)
    weapons = [result_to_dict(w) for w in weapons_q] or raise404()
    return jsonify(weapons)


@bp.route("/players")
def api_players():
    """
    Return a list of players.
    """
    players_q = db.session \
        .query(db.distinct(GamePlayer.handle).label('handle')) \
        .filter(GamePlayer.handle.isnot(None)) \
        .order_by(GamePlayer.game_id.desc())
    players_q = page(players_q).subquery()

    games_q = db.session.query(GamePlayer.handle, GamePlayer.game_id) \
        .join(players_q, players_q.c.handle == GamePlayer.handle) \
        .order_by(GamePlayer.game_id.desc())

    return jsonify({"players": list(game_ids(games_q, 'handle').values())})


@bp.route("/players/<string:handle>")
def api_player(handle):
    """
    Return a single player.
    """
    games_q = db.session \
        .query(GamePlayer.game_id) \
        .filter(GamePlayer.handle == handle)
    game_ids = [g.game_id for g in games_q] or raise404()
    return jsonify({'handle': handle,
                    'game_ids': game_ids})


@bp.route("/player:games/<string:handle>")
def api_player_games(handle):
    """
    Return a single player's games.
    """
    games_q = Game.query \
        .options(db.subqueryload(Game.players)) \
        .options(db.subqueryload(Game.teams)) \
        .options(db.subqueryload(Game.captures)) \
        .options(db.subqueryload(Game.bombings)) \
        .options(db.subqueryload(Game.ffarounds)) \
        .join(GamePlayer) \
        .filter(GamePlayer.handle == handle) \
        .order_by(Game.id.desc())
    games_q = page(games_q)
    games = [g.to_dict() for g in games_q] or raise404()
    return jsonify({'games': games})


@bp.route("/player:weapons/<string:handle>")
def api_player_weapons(handle):
    """
    Return a single player's weapons.
    """
    weapons_q = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.flakhits1).label('flakhits1'),
            db.func.sum(GameWeapon.flakhits2).label('flakhits2'),
            db.func.sum(GameWeapon.flakshots1).label('flakshots1'),
            db.func.sum(GameWeapon.flakshots2).label('flakshots2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2'),
            db.func.sum(GameWeapon.hits1).label('hits1'),
            db.func.sum(GameWeapon.hits2).label('hits2'),
            db.func.sum(GameWeapon.shots1).label('shots1'),
            db.func.sum(GameWeapon.shots2).label('shots2'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded')) \
        .filter(GameWeapon.playerhandle == handle) \
        .group_by(GameWeapon.weapon)
    weapons = [result_to_dict(w) for w in weapons_q] or raise404()
    return jsonify(weapons)


@bp.route("/player:game:weapons/<string:handle>/<int:gameid>")
def api_game_player_weapons(handle, gameid):
    """
    Return a single game player's weapons.
    """
    weapons_q = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.flakhits1).label('flakhits1'),
            db.func.sum(GameWeapon.flakhits2).label('flakhits2'),
            db.func.sum(GameWeapon.flakshots1).label('flakshots1'),
            db.func.sum(GameWeapon.flakshots2).label('flakshots2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2'),
            db.func.sum(GameWeapon.hits1).label('hits1'),
            db.func.sum(GameWeapon.hits2).label('hits2'),
            db.func.sum(GameWeapon.shots1).label('shots1'),
            db.func.sum(GameWeapon.shots2).label('shots2'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded')) \
        .filter(GameWeapon.game_id == gameid) \
        .filter(GameWeapon.playerhandle == handle) \
        .group_by(GameWeapon.weapon)
    weapons = [result_to_dict(w) for w in weapons_q] or raise404()
    return jsonify(weapons)


@bp.route("/servers")
def api_servers():
    """
    Return a list of players.
    """
    servers_q = db.session \
        .query(db.distinct(GameServer.handle).label('handle')) \
        .order_by(GameServer.game_id.desc())
    servers_q = page(servers_q).subquery()

    games_q = db.session.query(GameServer.handle, GameServer.game_id) \
        .join(servers_q, servers_q.c.handle == GameServer.handle) \
        .order_by(GameServer.game_id.desc())

    return jsonify({"servers": list(game_ids(games_q, 'handle').values())})


@bp.route("/servers/<string:handle>")
def api_server(handle):
    """
    Return a single server.
    """
    games_q = db.session \
        .query(GameServer.game_id) \
        .filter(GameServer.handle == handle)
    game_ids = [g.game_id for g in games_q] or raise404()
    return jsonify({'handle': handle,
                    'game_ids': game_ids})


@bp.route("/server:games/<string:handle>")
def api_server_games(handle):
    """
    Return a single server's games.
    """
    games_q = Game.query \
        .options(db.subqueryload(Game.players)) \
        .options(db.subqueryload(Game.teams)) \
        .options(db.subqueryload(Game.captures)) \
        .options(db.subqueryload(Game.bombings)) \
        .options(db.subqueryload(Game.ffarounds)) \
        .join(GameServer) \
        .filter(GameServer.handle == handle) \
        .order_by(Game.id.desc())
    games_q = page(games_q)
    games = [g.to_dict() for g in games_q] or raise404()
    return jsonify({'games': games})


@bp.route("/maps")
def api_maps():
    """
    Return a list of maps.
    """
    maps_q = db.session \
        .query(db.distinct(Game.map).label('map')) \
        .order_by(Game.id.desc())
    maps_q = page(maps_q).subquery()

    games_q = db.session.query(Game.map, Game.id) \
        .join(maps_q, maps_q.c.map == Game.map) \
        .order_by(Game.id.desc())

    topraces_limit = current_app.config['API_HIGHSCORE_RESULTS']

    maps = game_ids(games_q, 'name')
    for name, map in maps.items():
        map['topraces'] = rankings.map_topraces(name,
                endurance=False, limit=topraces_limit)

    return jsonify({"maps": list(maps.values())})


@bp.route("/maps/<string:name>")
def api_map(name):
    """
    Return a single map.
    """
    games_q = db.session.query(Game.id) \
        .filter(Game.map == name) \
        .order_by(Game.id.desc())
    game_ids = [g.id for g in games_q] or raise404()

    return jsonify({
        'name': name,
        'game_ids': game_ids,
        'topraces': rankings.map_topraces(name, endurance=False,
            limit=current_app.config['API_HIGHSCORE_RESULTS'])
    })


@bp.route("/map:games/<string:name>")
def api_map_games(name):
    """
    Return a single map's games.
    """
    games_q = Game.query \
        .options(db.joinedload(Game.players)) \
        .options(db.joinedload(Game.teams)) \
        .options(db.joinedload(Game.ffarounds)) \
        .options(db.joinedload(Game.captures)) \
        .options(db.joinedload(Game.bombings)) \
        .filter(Game.map == name) \
        .order_by(Game.id.desc())
    games = [g.to_dict() for g in page(games_q)] or raise404()

    return jsonify({"games": games})


@bp.route("/weapons")
def api_weapons():
    weapons_q = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.flakhits1).label('flakhits1'),
            db.func.sum(GameWeapon.flakhits2).label('flakhits2'),
            db.func.sum(GameWeapon.flakshots1).label('flakshots1'),
            db.func.sum(GameWeapon.flakshots2).label('flakshots2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2'),
            db.func.sum(GameWeapon.hits1).label('hits1'),
            db.func.sum(GameWeapon.hits2).label('hits2'),
            db.func.sum(GameWeapon.shots1).label('shots1'),
            db.func.sum(GameWeapon.shots2).label('shots2'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded')) \
        .group_by(GameWeapon.weapon)
    return jsonify([result_to_dict(w) for w in weapons_q])


@bp.route("/weapons/<string:name>")
def api_weapon(name):
    weapon = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.flakhits1).label('flakhits1'),
            db.func.sum(GameWeapon.flakhits2).label('flakhits2'),
            db.func.sum(GameWeapon.flakshots1).label('flakshots1'),
            db.func.sum(GameWeapon.flakshots2).label('flakshots2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2'),
            db.func.sum(GameWeapon.hits1).label('hits1'),
            db.func.sum(GameWeapon.hits2).label('hits2'),
            db.func.sum(GameWeapon.shots1).label('shots1'),
            db.func.sum(GameWeapon.shots2).label('shots2'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded')) \
        .filter(GameWeapon.weapon == name) \
        .one()
    if weapon.name is None:
        raise NotFound
    return jsonify(result_to_dict(weapon))


@bp.route("/modes")
def api_modes():
    modes = {}
    modes_q = db.session.query(Game.mode_id, Game.id) \
            .order_by(Game.id.desc())
    for mid, gid in modes_q:
        name = Mode.get(mid).name
        modes.setdefault(name, {'name': name, 'game_ids': []})
        modes[name]['game_ids'].append(gid)
    return jsonify(modes)


@bp.route("/modes/<string:name>")
def api_mode(name):
    mode = getattr(Mode, name, None) or raise404()
    game_ids = db.session.query(Game.id) \
            .filter(Game.mode_id == mode.id) \
            .order_by(Game.id.desc())
    return jsonify({'name': mode.name,
                    'game_ids': [g.id for g in game_ids]})


@bp.route("/mutators")
def api_mutators():
    muts = {}
    muts_q = GameMutator.query.order_by(GameMutator.game_id.desc())
    for gm in muts_q:
        name = Mutator.get(gm.mutator_id).link
        muts.setdefault(name, {'name': name, 'game_ids': []})
        muts[name]['game_ids'].append(gm.game_id)
    return jsonify(muts)


@bp.route("/mutators/<string:name>")
def api_mutator(name):
    mut = Mutator.by_link(name) or raise404()
    mut_q = db.session.query(GameMutator.game_id) \
            .filter_by(mutator_id=mut.id) \
            .order_by(GameMutator.game_id.desc())
    game_ids = [gid for gid, in mut_q]
    return jsonify({'name': mut.link, 'game_ids': game_ids})
