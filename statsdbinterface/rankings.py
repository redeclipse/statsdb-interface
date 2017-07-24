from . import weapon
from .database.models import Game, Mode, GameWeapon, GamePlayer, \
        GameMutator, Mutator, GameServer
from .database.core import db
from .function_cache import cached


@cached(15 * 60)
def weapon_sums(days):
    """
    Cache can be high, result will not change quickly.
    """
    first_game = Game.first_in_days(days)

    damage = db.func.sum(GameWeapon.damage1 + GameWeapon.damage2)
    timewielded = db.func.sum(GameWeapon.timewielded)

    return db.session \
        .query(GameWeapon.weapon,
               damage.label('damage'),
               timewielded.label('timewielded')) \
        .select_from(GameWeapon).join(Game) \
        .filter(Game.id >= first_game) \
        .filter(Game.normalweapons == 1) \
        .filter(GameWeapon.weapon.in_(weapon.loadout)) \
        .group_by(GameWeapon.weapon) \
        .all()


def weapons_by_wielded(days):
    """
    Return weapons sorted by wielded ratio.
    """
    weapons = weapon_sums(days)
    totalwielded = sum(w.timewielded for w in weapons)

    by_wielded = [{'name': w.weapon,
                   'timewielded': w.timewielded / totalwielded}
                  for w in weapons]
    by_wielded.sort(key=lambda w: w['timewielded'],
                    reverse=True)

    return by_wielded


def weapons_by_dpm(days):
    """
    Return weapons sorted by DPM.
    """
    weapons = weapon_sums(days)

    by_dpm = [{'name': w.weapon,
               'dpm': w.damage / (w.timewielded / 60)}
              for w in weapons]
    by_dpm.sort(key=lambda w: w['dpm'], reverse=True)

    return by_dpm


@cached(3 * 60)
def maps_by_playertime(days, limit):
    """
    Return maps sorted by their player time.
    """
    first_game = Game.first_in_days(days)
    q1 = db.session.query(
            Game.map.label('name'),
            db.func.count(Game.id).label('games')) \
        .filter(Game.id >= first_game) \
        .group_by(Game.map) \
        .subquery()
    q2 = db.session.query(
            Game.map,
            db.func.sum(GamePlayer.timeactive).label('time')) \
        .select_from(Game).join(GamePlayer) \
        .filter(Game.id >= first_game) \
        .group_by(Game.map) \
        .subquery()
    return db.session.query(q1.c.name, q1.c.games, q2.c.time) \
        .select_from(q1).join(q2, q1.c.name == q2.c.map) \
        .order_by(q2.c.time.desc()) \
        .limit(limit).all()


@cached(60)
def players_by_games(days, limit):
    first_game = Game.first_in_days(days)
    return db.session.query(
            GamePlayer.handle,
            db.func.count().label('games')) \
        .filter(GamePlayer.game_id >= first_game) \
        .filter(GamePlayer.handle.isnot(None)) \
        .order_by(db.func.count().desc()) \
        .group_by(GamePlayer.handle) \
        .limit(limit)


@cached(60)
def modes_by_games(days=None):
    since = True if days is None else Game.id >= Game.first_in_days(days)
    modes = Mode.query \
        .filter(Mode.name.notin_(['edit', 'demo'])) \
        .all()
    modes = [{'name': m.name,
              'longname': m.longname,
              'games': m.games.filter(since).count()}
             for m in modes]
    modes.sort(key=lambda m: m['games'], reverse=True)
    return modes


@cached(60)
def mutators_by_games(days=None):
    since = True if days is None else Game.id >= Game.first_in_days(days)
    mutators = db.session.query(Mutator,
                                db.func.count(Game.id)) \
        .join(Mutator.games) \
        .filter(since) \
        .group_by(Mutator.id) \
        .order_by(db.func.count(Game.id).desc()) \
        .all()
    return [{'name': mutator.name,
             'link': mutator.link,
             'shortname': mutator.shortname,
             'games': game_count}
            for mutator, game_count in mutators]


@cached(60)
def servers_by_games(days, limit):
    first_game = Game.first_in_days(days)
    return db.session.query(
            GameServer.handle,
            db.func.count(GameServer.game_id).label('games')) \
        .filter(GameServer.game_id >= first_game) \
        .group_by(GameServer.handle) \
        .order_by(db.func.count(GameServer.game_id).desc()) \
        .limit(limit).all()


@cached(5 * 60)
def players_by_damage(days):
    first_game = Game.first_in_days(days)

    q1 = db.session.query(
            GamePlayer.handle,
            db.func.sum(GamePlayer.timealive).label('timealive'),
            db.func.sum(GamePlayer.frags).label('frags'),
            db.func.count(GamePlayer.game).label('games')) \
        .join(Game) \
        .filter(GamePlayer.game_id >= first_game) \
        .filter(GamePlayer.handle.isnot(None)) \
        .filter(Game.normalweapons == 1) \
        .filter(Game.uniqueplayers > 1) \
        .group_by(GamePlayer.handle) \
        .subquery()

    q2 = db.session.query(
            GameWeapon.playerhandle.label('handle'),
            db.func.sum(GameWeapon.damage1
                        + GameWeapon.damage2).label('damage')) \
        .join(Game) \
        .filter(GameWeapon.game_id >= first_game) \
        .filter(GameWeapon.playerhandle.isnot(None)) \
        .filter(Game.normalweapons == 1) \
        .filter(Game.uniqueplayers > 1) \
        .filter(GameWeapon.weapon.notin_(weapon.not_wielded)) \
        .group_by(GameWeapon.playerhandle) \
        .subquery()

    data = db.session.query(
            q1.c.handle,
            q1.c.games,
            (q2.c.damage / (q1.c.timealive / 60)).label('dpm'),
            (q2.c.damage / q1.c.frags).label('dpf')) \
        .select_from(q1).join(q2, q1.c.handle == q2.c.handle) \
        .all()

    min_games = sum(p.games for p in data if p.games is not None)
    min_games /= len(data)
    min_games /= 2

    data = [p for p in data if p.games > min_games]

    by_dpm = [p for p in data if p.dpm is not None]
    by_dpm.sort(key=lambda p: p.dpm, reverse=True)

    by_dpf = [p for p in data if p.dpf is not None]
    by_dpf.sort(key=lambda p: p.dpf)

    return by_dpm, by_dpf


def players_by_dpm(days):
    """
    Return a sorted list of players with and by dpm.
    """
    return players_by_damage(days)[0]


def players_by_dpf(days):
    """
    Return a sorted list of players with and by dpf.
    """
    return players_by_damage(days)[1]


@cached(60)
def players_by_kdr(days):
    first_game = Game.first_in_days(days)
    data = db.session.query(
            GamePlayer.handle,
            db.func.sum(GamePlayer.frags).label('frags'),
            db.func.sum(GamePlayer.deaths).label('deaths')) \
        .join(Game) \
        .filter(GamePlayer.game_id >= first_game) \
        .filter(GamePlayer.handle.isnot(None)) \
        .filter(Game.uniqueplayers > 1) \
        .filter(Game.mode.in_([Mode.bb, Mode.ctf, Mode.dac, Mode.dm])) \
        .group_by(GamePlayer.handle)

    by_kdr = [{'handle': p.handle, 'kdr': p.frags / p.deaths}
              for p in data
              if p.deaths > 0]
    by_kdr.sort(key=lambda p: p['kdr'], reverse=True)

    return by_kdr


def _nub_races(races_q, limit):
    """ Can't use `.group_by(GamePlayer.handle).having()` or all
    players without a handle will have just one position in the
    top.
    Takes only the first race in `races_q` for each player, i.e.
    assumes `races_q` is ordered.
    """
    races = []
    names = set()
    for race in races_q:
        player = race.handle or race.name
        if player in names:
            continue
        names.add(player)
        races.append(race)
        if len(races) >= limit:
            break
    return races


def map_topraces(name, endurance, limit):
    not_freestyle = ~Game.mutator_ids.any(mutator_id=Mutator.freestyle.id)
    if endurance:
        race_timed = db.and_(
            Game.mutator_ids.any(mutator_id=Mutator.race_timed.id),
            Game.mutator_ids.any(mutator_id=Mutator.race_endurance.id))
    else:
        race_timed = GameMutator.mutator_id == Mutator.race_timed.id

    top_races_q = db.session \
        .query(Game.id.label('game_id'),
               Game.time.label('when'),
               GamePlayer.score,
               GamePlayer.name,
               GamePlayer.handle) \
        .select_from(Game) \
        .join(GameMutator) \
        .join(GamePlayer) \
        .filter(Game.map == name) \
        .filter(race_timed) \
        .filter(not_freestyle) \
        .filter(GamePlayer.score > 0) \
        .order_by(GamePlayer.score.asc())

    return _nub_races(top_races_q, limit=limit)
