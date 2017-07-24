import time
from datetime import datetime, timezone

from flask import Blueprint, render_template, send_from_directory, \
        current_app
from werkzeug.exceptions import NotFound

from . import templateutils
from .. import rankings, weapon
from ..database.models import Game, GamePlayer, GameServer, GameWeapon, \
    GameMutator, Mode, Mutator
from ..database.core import db
from ..utils import recent, pager, raise404, days_ago
from ..function_cache import cached


# displays blueprint
bp = Blueprint(__name__, __name__)


@bp.route('/static/<path:path>')
def static(path):
    return send_from_directory('static', path)


@bp.route("/")
def display_dashboard():
    short, long = 7, 30
    ranks = {
        'players_by_games': rankings.players_by_games(days=short, limit=5),
        'servers_by_games': rankings.servers_by_games(days=short, limit=5),
        'players_by_dpm': rankings.players_by_dpm(days=short),
        'players_by_dpf': rankings.players_by_dpf(days=short),
        'maps_by_playertime': rankings.maps_by_playertime(days=long, limit=5),
        'weapons_by_wielded': rankings.weapons_by_wielded(days=long),
        'weapons_by_dpm': rankings.weapons_by_dpm(days=long),
        'players_by_kdr': rankings.players_by_kdr(days=long),
    }
    return render_template('displays/dashboard.html',
                           games=recent(Game.list),
                           short=short,
                           long=long,
                           **ranks)


@bp.route("/games")
def display_games():
    game_count, gametime = db.session \
        .query(db.func.count(),
               db.func.sum(Game.timeplayed)) \
        .one()
    playertime = db.session \
        .query(db.func.sum(GamePlayer.timeactive)) \
        .scalar()
    return render_template('displays/games.html',
                           pager=pager(Game.list, lambda: game_count),
                           game_count=game_count,
                           gametime=gametime,
                           playertime=playertime)


@bp.route("/game/<int:gameid>")
@bp.route("/games/<int:gameid>")
def display_game(gameid):
    game = Game.query \
        .options(db.joinedload(Game.players)) \
        .get_or_404(gameid)

    args = {}
    if not game.is_peaceful():
        weapons = db.session.query(
                GameWeapon.weapon.label('name'),
                db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
                db.func.sum(GameWeapon.timewielded).label('timewielded'),
                db.func.sum(GameWeapon.damage1).label('damage1'),
                db.func.sum(GameWeapon.damage2).label('damage2'),
                db.func.sum(GameWeapon.frags1).label('frags1'),
                db.func.sum(GameWeapon.frags2).label('frags2')) \
            .filter(GameWeapon.game_id == gameid) \
            .group_by(GameWeapon.weapon) \
            .all()
        args['weapons'] = weapon.ordered(weapons)

        damage = db.session.query(
                GameWeapon.player.label('wid'),
                db.func.sum(GameWeapon.damage1
                            + GameWeapon.damage2).label('damage')) \
            .filter(GameWeapon.game_id == gameid) \
            .group_by(GameWeapon.player)
        args['damage'] = {p.wid: p.damage for p in damage}

        args['totalwielded'] = sum(w['timewielded'] for w in args['weapons'])

    return render_template('displays/game.html', game=game, **args)


@bp.route("/servers")
def display_servers():
    q1 = db.session \
        .query(GameServer.handle,
               db.func.count().label('game_count'),
               db.func.min(GameServer.game_id).label('first_game'),
               db.func.max(GameServer.game_id).label('last_game')) \
        .group_by(GameServer.handle) \
        .subquery()
    gs = db.aliased(GameServer)
    first_game = db.aliased(Game)
    last_game = db.aliased(Game)
    servers_q = db.session \
        .query(q1,
               gs.desc.label('last_desc'),
               first_game.time.label('first_time'),
               last_game.time.label('last_time')) \
        .join(gs, q1.c.last_game == gs.game_id) \
        .join(first_game, q1.c.first_game == first_game.id) \
        .join(last_game, q1.c.last_game == last_game.id) \
        .order_by(q1.c.last_game.desc())

    count = db.session \
        .query(db.distinct(GameServer.handle)) \
        .count

    return render_template('displays/servers.html',
                           pager=pager(servers_q, count))


@bp.route("/server/<string:handle>")
@bp.route("/servers/<string:handle>")
def display_server(handle):
    server_q = db.session \
        .query(GameServer.handle,
               db.func.min(GameServer.game_id).label('first_game'),
               db.func.max(GameServer.game_id).label('last_game'),
               db.func.count(GameServer.game_id).label('game_count')) \
        .filter(GameServer.handle == handle) \
        .subquery()

    first_game_q = db.aliased(Game)
    last_game_q = db.aliased(Game)
    last_server_q = db.aliased(GameServer)

    server = db.session \
        .query(server_q,
               first_game_q.time.label('first_time'),
               last_game_q.time.label('last_time'),
               last_server_q.desc.label('last_desc'),
               last_server_q.host.label('last_host'),
               last_server_q.port.label('last_port')) \
        .select_from(server_q) \
        .join(first_game_q,
              db.and_(server_q.c.first_game == first_game_q.id)) \
        .join(last_game_q,
              db.and_(server_q.c.last_game == last_game_q.id)) \
        .join(last_server_q,
              db.and_(server_q.c.last_game == last_server_q.game_id)) \
        .one_or_none()

    if server is None:
        raise NotFound

    games_q = Game.list \
        .join(GameServer) \
        .filter(GameServer.handle == handle)

    return render_template('displays/server.html',
                           server=server,
                           games=recent(games_q))


@bp.route("/server:games/<string:handle>")
def display_server_games(handle):
    games_q = Game.list \
        .join(GameServer) \
        .filter(GameServer.handle == handle)

    count = GameServer.query \
        .filter(GameServer.handle == handle) \
        .count

    return render_template('displays/server_games.html',
                           server={'handle': handle},
                           pager=pager(games_q, count))


@bp.route("/players")
def display_players():
    player_q = db.session.query(
            GamePlayer.handle,
            db.func.min(GamePlayer.game_id).label('first_game'),
            db.func.max(GamePlayer.game_id).label('last_game'),
            db.func.count(GamePlayer.game_id).label('game_count')) \
        .filter(GamePlayer.handle.isnot(None)) \
        .group_by(GamePlayer.handle) \
        .subquery()

    last_q = db.session.query(GamePlayer.game_id,
                              GamePlayer.handle,
                              GamePlayer.name,
                              Game.time) \
        .select_from(GamePlayer).join(Game) \
        .subquery()

    first_q = db.session.query(GamePlayer.game_id,
                               GamePlayer.handle,
                               Game.time) \
        .select_from(GamePlayer).join(Game) \
        .subquery()

    q = db.session.query(player_q,
                         last_q.c.name,
                         last_q.c.time.label('last_time'),
                         first_q.c.time.label('first_time')) \
        .select_from(player_q) \
        .join(last_q, db.and_(player_q.c.last_game == last_q.c.game,
                              player_q.c.handle == last_q.c.handle)) \
        .join(first_q, db.and_(player_q.c.first_game == first_q.c.game,
                               player_q.c.handle == first_q.c.handle)) \
        .order_by(player_q.c.last_game.desc())

    count = db.session.query(db.distinct(GamePlayer.handle)).count

    return render_template('displays/players.html', pager=pager(q, count))


@bp.route("/player/<string:handle>")
@bp.route("/players/<string:handle>")
def display_player(handle):
    player_q = db.session.query(
            GamePlayer.handle,
            db.func.min(GamePlayer.game_id).label('first_game'),
            db.func.max(GamePlayer.game_id).label('last_game'),
            db.func.count(GamePlayer.game_id).label('game_count')) \
        .filter(GamePlayer.handle == handle) \
        .group_by(GamePlayer.handle) \
        .subquery()

    last_q = db.session.query(GamePlayer.game_id,
                              GamePlayer.handle,
                              GamePlayer.name,
                              Game.time) \
        .select_from(GamePlayer).join(Game) \
        .subquery()

    first_q = db.session.query(GamePlayer.game_id,
                               GamePlayer.handle,
                               Game.time) \
        .select_from(GamePlayer).join(Game) \
        .subquery()

    player = db.session.query(
            player_q,
            last_q.c.name,
            last_q.c.time.label('last_time'),
            first_q.c.time.label('first_time')) \
        .select_from(player_q) \
        .join(last_q, db.and_(player_q.c.last_game == last_q.c.game,
                              player_q.c.handle == last_q.c.handle)) \
        .join(first_q, db.and_(player_q.c.first_game == first_q.c.game,
                               player_q.c.handle == first_q.c.handle)) \
        .order_by(player_q.c.last_game.desc()) \
        .one_or_none()

    if player is None:
        raise NotFound

    topmap = db.session \
        .query(Game.map, db.func.count().label('game_count')) \
        .join(GamePlayer) \
        .filter(GamePlayer.handle == handle) \
        .group_by(Game.map) \
        .order_by(db.func.count().desc()) \
        .first()

    games_q = GamePlayer.query \
        .join(Game) \
        .filter(GamePlayer.handle == handle) \
        .filter(Game.uniqueplayers > 1) \
        .filter(Game.normalweapons == 1) \
        .limit(50)

    timealive, frags, deaths = 0, 0, 0
    for g in games_q:
        timealive += g.timealive
        frags += g.frags
        deaths += g.deaths

    games_q = games_q.subquery()
    weapons = db.session.query(
            GameWeapon.weapon.label('name'),
            db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
            db.func.sum(GameWeapon.timewielded).label('timewielded'),
            db.func.sum(GameWeapon.damage1).label('damage1'),
            db.func.sum(GameWeapon.damage2).label('damage2'),
            db.func.sum(GameWeapon.frags1).label('frags1'),
            db.func.sum(GameWeapon.frags2).label('frags2')) \
        .select_from(games_q) \
        .join(GameWeapon,
              db.and_(games_q.c.game == GameWeapon.game_id,
                      games_q.c.wid == GameWeapon.player)) \
        .group_by(GameWeapon.weapon) \
        .all()

    totalwielded, damage = 0, 0
    for w in weapons:
        totalwielded += w.timewielded
        damage += w.damage1 + w.damage2

    games_q = Game.list \
        .join(GamePlayer) \
        .filter(GamePlayer.handle == handle)

    dpm = damage / (timealive / 60) if timealive > 0 else 0
    fpm = frags / (timealive / 60) if timealive > 0 else 0
    kdr = frags / deaths if deaths > 0 else 0
    dfr = damage / frags if frags > 0 else 0

    return render_template('displays/player.html',
                           player=player,
                           games=recent(games_q),
                           topmap=topmap,
                           dpm=dpm,
                           fpm=fpm,
                           kdr=kdr,
                           dfr=dfr,
                           weapons=weapon.ordered(weapons),
                           totalwielded=totalwielded)


@bp.route("/player:games/<string:handle>")
def display_player_games(handle):
    games_q = Game.list \
        .join(GamePlayer) \
        .filter(GamePlayer.handle == handle)
    return render_template('displays/player_games.html',
                           player={'handle': handle},
                           pager=pager(games_q))


@bp.route("/maps")
def display_maps():
    maps_q = db.session \
        .query(Game.map.label('name'),
               db.func.min(Game.id).label('first_game'),
               db.func.max(Game.id).label('last_game'),
               db.func.count(Game.id).label('game_count')) \
        .group_by(Game.map) \
        .subquery()

    race_timed = GameMutator.mutator_id == Mutator.race_timed.id
    not_freestyle = ~Game.mutator_ids.any(mutator_id=Mutator.freestyle.id)

    races_q = db.session \
        .query(Game.map,
               Game.id.label('top_race'),
               GamePlayer.score.label('top_race_score'),
               GamePlayer.name.label('top_race_name'),
               GamePlayer.handle.label('top_race_handle')) \
        .select_from(Game) \
        .join(GameMutator) \
        .join(GamePlayer) \
        .filter(race_timed) \
        .filter(not_freestyle) \
        .filter(GamePlayer.score > 0) \
        .order_by(Game.map, GamePlayer.score.desc()) \
        .subquery()

    top_races_q = db.session.query(races_q).group_by(races_q.c.map).subquery()

    first_q = db.aliased(Game)
    last_q = db.aliased(Game)

    q = db.session \
        .query(maps_q,
               first_q.time.label('first_time'),
               last_q.time.label('last_time'),
               top_races_q.c.top_race,
               top_races_q.c.top_race_score,
               top_races_q.c.top_race_name,
               top_races_q.c.top_race_handle) \
        .join(first_q, maps_q.c.first_game == first_q.id) \
        .join(last_q, maps_q.c.last_game == last_q.id) \
        .outerjoin(top_races_q, maps_q.c.name == top_races_q.c.map) \
        .order_by(maps_q.c.last_game.desc())

    count = db.session.query(db.distinct(Game.map)).count

    return render_template('displays/maps.html', pager=pager(q, count))


@bp.route("/racemaps")
def display_racemaps():
    maps_q = db.session \
        .query(Game.map.label('name'),
               db.func.min(Game.id).label('first_game'),
               db.func.max(Game.id).label('last_game'),
               db.func.count(Game.id).label('game_count')) \
        .group_by(Game.map) \
        .subquery()

    race_timed = GameMutator.mutator_id == Mutator.race_timed.id
    not_freestyle = ~Game.mutator_ids.any(mutator_id=Mutator.freestyle.id)

    races_q = db.session \
        .query(Game.map,
               Game.id.label('top_race'),
               GamePlayer.score.label('top_race_score'),
               GamePlayer.name.label('top_race_name'),
               GamePlayer.handle.label('top_race_handle')) \
        .select_from(Game) \
        .join(GameMutator) \
        .join(GamePlayer) \
        .filter(race_timed) \
        .filter(not_freestyle) \
        .filter(GamePlayer.score > 0) \
        .order_by(Game.map, GamePlayer.score.desc()) \
        .subquery()

    top_races_q = db.session.query(races_q).group_by(races_q.c.map).subquery()

    count = db.session \
        .query(db.distinct(Game.map)) \
        .join(GameMutator) \
        .filter(race_timed) \
        .count

    race_timed = db.and_(
        Game.mutator_ids.any(mutator_id=Mutator.race_timed.id),
        Game.mutator_ids.any(mutator_id=Mutator.race_endurance.id))

    races_q = db.session \
        .query(Game.map,
               Game.id.label('top_endurance_race'),
               GamePlayer.score.label('top_endurance_race_score'),
               GamePlayer.name.label('top_endurance_race_name'),
               GamePlayer.handle.label('top_endurance_race_handle')) \
        .select_from(Game) \
        .join(GameMutator) \
        .join(GamePlayer) \
        .filter(race_timed) \
        .filter(not_freestyle) \
        .filter(GamePlayer.score > 0) \
        .order_by(Game.map, GamePlayer.score.desc()) \
        .subquery()

    top_endurance_races_q = db.session.query(races_q).group_by(races_q.c.map) \
        .subquery()

    first_q = db.aliased(Game)
    last_q = db.aliased(Game)

    q = db.session \
        .query(maps_q,
               first_q.time.label('first_time'),
               last_q.time.label('last_time'),
               top_races_q.c.top_race,
               top_races_q.c.top_race_score,
               top_races_q.c.top_race_name,
               top_races_q.c.top_race_handle,
               top_endurance_races_q.c.top_endurance_race,
               top_endurance_races_q.c.top_endurance_race_score,
               top_endurance_races_q.c.top_endurance_race_name,
               top_endurance_races_q.c.top_endurance_race_handle) \
        .join(first_q, maps_q.c.first_game == first_q.id) \
        .join(last_q, maps_q.c.last_game == last_q.id) \
        .join(top_races_q, maps_q.c.name == top_races_q.c.map) \
        .outerjoin(top_endurance_races_q,
                   maps_q.c.name == top_endurance_races_q.c.map) \
        .order_by(maps_q.c.last_game.desc())

    return render_template('displays/racemaps.html',
                           pager=pager(q, count))


@bp.route("/map/<string:name>")
@bp.route("/maps/<string:name>")
def display_map(name):
    map_q = db.session \
        .query(Game.map.label('name'),
               db.func.min(Game.id).label('first_game'),
               db.func.max(Game.id).label('last_game'),
               db.func.count(Game.id).label('game_count'),
               db.func.sum(Game.timeplayed).label('time_played')) \
        .filter(Game.map == name) \
        .group_by(Game.map) \

    map_q = map_q.subquery()

    first_q = db.aliased(Game)
    last_q = db.aliased(Game)

    map = db.session.query(map_q,
                           first_q.time.label('first_time'),
                           last_q.time.label('last_time')) \
        .select_from(map_q) \
        .join(first_q, map_q.c.first_game == first_q.id) \
        .join(last_q, map_q.c.last_game == last_q.id) \
        .one_or_none()

    if map is None:
        raise NotFound

    player_time = db.session \
        .query(db.func.sum(GamePlayer.timeactive)) \
        .join(Game) \
        .filter(Game.map == name) \
        .scalar()

    topraces_limit = current_app.config['DISPLAY_HIGHSCORE_RESULTS']
    top_races = rankings.map_topraces(name, endurance=False,
                                      limit=topraces_limit)
    top_endurance_races = rankings.map_topraces(name, endurance=True,
                                                limit=topraces_limit)

    games_q = Game.list.filter(Game.map == name)

    return render_template('displays/map.html',
                           map=map,
                           player_time=player_time,
                           games=recent(games_q),
                           top_races=top_races,
                           top_endurance_races=top_endurance_races)


@bp.route("/map:games/<string:name>")
def display_map_games(name):
    q = Game.query \
        .options(db.joinedload(Game.players)) \
        .order_by(Game.id.desc()) \
        .filter(Game.map == name)
    return render_template('displays/map_games.html',
                           map={'name': name},
                           pager=pager(q))


@bp.route("/modes")
def display_modes():
    days = 30
    return render_template('displays/modes.html',
                           all=rankings.modes_by_games(),
                           recent_days=days,
                           recent=rankings.modes_by_games(days))


@bp.route("/mode/<string:name>")
@bp.route("/modes/<string:name>")
def display_mode(name):
    mode = getattr(Mode, name, None) or raise404()
    games_q = Game.list.filter(Game.mode_id == mode.id)
    game_count = games_q.count()
    return render_template('displays/mode.html',
                           mode=mode,
                           game_count=game_count,
                           games=recent(games_q))


@bp.route("/mode:games/<string:name>")
def display_mode_games(name):
    mode = getattr(Mode, name, None) or raise404()
    games_q = Game.list.filter(Game.mode_id == mode.id)
    return render_template('displays/mode_games.html',
                           mode=mode,
                           pager=pager(games_q))


@bp.route("/mutators")
def display_mutators():
    days = 30
    ret = render_template('displays/mutators.html',
                          all=rankings.mutators_by_games(),
                          recent_days=days,
                          recent=rankings.mutators_by_games(days))
    return ret


@bp.route("/mutator/<string:name>")
@bp.route("/mutators/<string:name>")
def display_mutator(name):
    mut = Mutator.by_link(name)
    games_q = Game.list.filter(Game.mutator_ids.any(mutator_id=mut.id))
    return render_template('displays/mutator.html',
                           mutator=mut,
                           game_count=games_q.count(),
                           games=recent(games_q))


@bp.route("/mutator:games/<string:name>")
def display_mutator_games(name):
    mut = Mutator.by_link(name) or raise404()
    games_q = Game.list.filter(Game.mutator_ids.any(mutator_id=mut.id))
    return render_template('displays/mutator_games.html',
                           mutator=mut,
                           pager=pager(games_q))


@bp.route("/weapons")
def display_weapons():
    recent_count = 300
    games_q = db.session \
        .query(Game.id) \
        .order_by(Game.id.desc()) \
        .filter(Game.uniqueplayers > 1) \
        .filter(Game.normalweapons == 1) \
        .limit(recent_count) \
        .subquery()
    weapons = db.session \
        .query(GameWeapon.weapon.label('name'),
               db.func.sum(GameWeapon.timeloadout).label('timeloadout'),
               db.func.sum(GameWeapon.timewielded).label('timewielded'),
               db.func.sum(GameWeapon.damage1).label('damage1'),
               db.func.sum(GameWeapon.damage2).label('damage2'),
               db.func.sum(GameWeapon.frags1).label('frags1'),
               db.func.sum(GameWeapon.frags2).label('frags2')) \
        .filter(GameWeapon.game_id.in_(games_q)) \
        .group_by(GameWeapon.weapon) \
        .all()

    totalwielded = sum(w.timewielded for w in weapons)

    return render_template('displays/weapons.html',
                           recent_count=recent_count,
                           weapons=weapon.ordered(weapons),
                           totalwielded=totalwielded)


@cached(60 * 60)
def active_minutes(days):
    day_len = 24 * 60 * 60
    since = days_ago(days)
    minutes_offset = int((since - ((since // day_len) * day_len)) // 60)
    first_game = Game.first_in_days(days)

    games = db.session \
        .query(Game.time.label('end'),
               Game.timeplayed.label('duration'),
               Game.uniqueplayers.label('player_count')) \
        .filter(Game.id >= first_game) \
        .all()

    max_minutes = round((time.time() - days_ago(days)) / 60) + 1
    by_minutes = [0] * max_minutes

    since = days_ago(days)

    def minutes(g):
        end_sec = g.end - since
        start_min = int((end_sec - g.duration) // 60)
        end_min = round(end_sec / 60)
        return range(start_min, end_min)

    for g in games:
        for m in minutes(g):
            by_minutes[m] += g.player_count

    return minutes_offset, by_minutes


@bp.route("/activehours")
def display_activehours():
    days = 30
    minutes_offset, by_minutes = active_minutes(days)

    by_hours = [0] * 24
    for m, player_count in enumerate(by_minutes):
        by_hours[((m + minutes_offset) // 60) % 24] += player_count
    for h, player_count in enumerate(by_hours):
        by_hours[h] = player_count / (days * 60)

    barfactor = 100 / max(by_hours)
    times = [{'label': hour,
              'players': player_count,
              'bar': '|' * round(player_count * barfactor)}
             for hour, player_count in enumerate(by_hours)]
    return render_template('displays/times.html',
                           days=days,
                           label="Hours",
                           times=times)


@bp.route("/activeweekdays")
def display_activeweekdays():
    days = 30
    minutes_offset, by_minutes = active_minutes(days)

    by_weekdays = [0] * 7
    weekday_len = [0] * 7
    for m, player_count in enumerate(by_minutes):
        day = ((m + minutes_offset) // (24 * 60)) % 7
        by_weekdays[day] += player_count
        weekday_len[day] += 1
    for d, minutes in enumerate(weekday_len):
        by_weekdays[d] /= minutes

    since = days_ago(days)
    mon = (7 - datetime.fromtimestamp(since, timezone.utc).weekday()) % 7
    by_weekdays = by_weekdays[mon:] + by_weekdays[:mon]

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    barfactor = 100 / max(by_weekdays)
    times = [{'label': weekdays[i],
              'players': players,
              'bar': '|' * round(players * barfactor)}
             for i, players in enumerate(by_weekdays)]

    return render_template('displays/times.html',
                           days=days,
                           label="Weekdays",
                           times=times)


@bp.route("/activeweekdayhours")
def display_activeweekdayhours():
    days = 30
    minutes_offset, by_minutes = active_minutes(days)

    weeklen = 7 * 24
    by_weekhours = [0] * weeklen
    weekhour_len = [0] * weeklen
    for m, player_count in enumerate(by_minutes):
        weekhour = ((m + minutes_offset) // 60) % weeklen
        by_weekhours[weekhour] += player_count
        weekhour_len[weekhour] += 1
    for wh, minutes in enumerate(weekhour_len):
        by_weekhours[wh] /= minutes

    start = datetime.fromtimestamp(days_ago(days), timezone.utc)
    mon0 = (weeklen - (start.weekday() * 24 + start.hour)) % weeklen
    by_weekhours = by_weekhours[mon0:] + by_weekhours[:mon0]

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    barfactor = 100 / max(by_weekhours)
    times = [{'label': '%s - %s' % (weekdays[i // 24], i % 24),
              'players': players,
              'bar': '|' * round(players * barfactor)}
             for i, players in enumerate(by_weekhours)]

    ret = render_template('displays/times.html',
                          days=days,
                          label="Weekday Hours",
                          times=times)
    return ret


templateutils.setup(bp)
