import time
from .database import models, extmodels
from .database.core import db
from .function_cache import cached
from . import redeclipse


def days_ago(days):
    return time.time() - (days * 60 * 60 * 24)


@cached(60)
def first_game_in_days(days):
    return (
        (models.Game.query
         .with_entities(db.func.min(models.Game.id))
         .filter(models.Game.time >= days_ago(days))).scalar() or
        (models.Game.query
         .with_entities(db.func.max(models.Game.id)).scalar() + 1)
        )


def weapon_sums(days, use_totalwielded=True):
    first_game = first_game_in_days(days)
    totalwielded = 0
    if use_totalwielded:
        totalwielded = (models.GameWeapon.query
                        .join(models.Game)
                        .with_entities(db.func.sum(
                            models.GameWeapon.timewielded))
                        .filter(models.GameWeapon.game_id >= first_game)
                        .filter(models.Game.normalweapons == 1)
                        .filter(models.GameWeapon.weapon.in_(
                            redeclipse.versions.default.standardweaponlist))
                        .first()[0])
    weapons = extmodels.Weapon.all_from_f((
        models.GameWeapon.game_id >= first_game,
        models.Game.normalweapons == 1,
        models.GameWeapon.weapon.in_(
            redeclipse.versions.default.standardweaponlist)))
    return {
         "weapons": weapons,
         "totalwielded": totalwielded or 0,
         }


@cached(15 * 60)
def weapons_by_wielded(days):
    """
    Return weapons sorted by wielded ratio.
    Cache can be high, result will not change quickly.
    """
    res = weapon_sums(days)
    ret = sorted(res["weapons"], key=lambda w: w.timewielded, reverse=True)
    return [{"name": w.name, "timewielded":
             w.timewielded / max(1, res["totalwielded"])} for w in ret]


@cached(15 * 60)
def weapons_by_dpm(days):
    """
    Return weapons sorted by DPM.
    Cache can be high, result will not change quickly.
    """
    res = weapon_sums(days, False)
    mintime = sum([w.time() for w in res["weapons"]]) / len(res["weapons"]) / 4
    ret = sorted([w for w in res["weapons"] if w.time() >= mintime],
                 key=lambda w: (w.damage1 + w.damage2) /
                 (max(1, w.time()) / 60), reverse=True)
    return [{"name": w.name, "dpm": (w.damage1 + w.damage2) /
             (max(1, w.time()) / 60)} for w in ret]


@cached(60 * 3)
def maps_by_playertime(days):
    """
    Return maps sorted by their player time.
    Cache should be low, result could change quickly.
    """
    first_game = first_game_in_days(days)
    maps = [r[0] for r in models.Game.query
            .with_entities(models.Game.map)
            .filter(models.Game.time >= days_ago(days))]
    ret = []
    for map_ in set(maps):
        ret.append({
            "name": map_,
            "time": (models.GamePlayer.query
                     .join(models.Game)
                     .with_entities(db.func.sum(models.GamePlayer.timeactive))
                     .filter(models.GamePlayer.game_id >= first_game)
                     .filter(models.Game.map == map_)
                     .first()[0]),
            "games": maps.count(map_),
            })
    return sorted(ret, key=lambda m: m['time'], reverse=True)


@cached(60)
def players_by_games(days):
    first_game = first_game_in_days(days)
    players = [r[0] for r in models.GamePlayer.query
               .with_entities(models.GamePlayer.handle)
               .filter(models.GamePlayer.game_id >= first_game)
               .filter(models.GamePlayer.handle != "")]
    ret = []
    for player in set(players):
        ret.append({
            "handle": player,
            "games": players.count(player),
            })
    return sorted(ret, key=lambda p: p['games'], reverse=True)


@cached(60)
def modes_by_games(days):
    first_game = first_game_in_days(days)
    modes = models.Mode.query \
        .filter(models.Mode.name.notin_(['edit', 'demo'])) \
        .all()
    ret = []
    for mode in modes:
        m = {'name': mode.name,
             'longname': mode.longname,
             'games': mode.games.filter(models.Game.id >= first_game)
                                .count()}
        ret.append(m)
    return sorted(ret, key=lambda m: m['games'], reverse=True)


@cached(60)
def mutators_by_games(days=None):
    first_game = 0 if days is None else first_game_in_days(days)
    mutators = db.session.query(models.Mutator,
                                db.func.count(models.Game.id)) \
        .join(models.Mutator.games) \
        .filter(models.Game.id >= first_game) \
        .group_by(models.Mutator.id) \
        .order_by(db.func.count(models.Game.id).desc()) \
        .all()
    ret = []
    for mutator, game_count in mutators:
        m = {
            'name': mutator.name,
            'link': mutator.link,
            'shortname': mutator.shortname,
            'games': game_count
        }
        ret.append(m)
    return ret


@cached(60)
def servers_by_games(days):
    first_game = first_game_in_days(days)
    servers = [r[0] for r in models.GameServer.query
               .with_entities(models.GameServer.handle)
               .filter(models.GameServer.game_id >= first_game)
               .filter(models.GameServer.handle != "")]
    ret = []
    for server in set(servers):
        ret.append({
            "handle": server,
            "games": servers.count(server),
            })
    return sorted(ret, key=lambda p: p['games'], reverse=True)


@cached(60)
def players_by_kdr(days):
    first_game = first_game_in_days(days)
    ret = {}
    games = {}
    for player in (models.GamePlayer.query.join(models.Game)
                   .filter(models.GamePlayer.game_id >= first_game)
                   .filter(models.GamePlayer.handle != "")
                   .filter(models.Game.uniqueplayers > 1)):
        if player.handle not in ret:
            ret[player.handle] = {
                "handle": player.handle,
                "frags": 0,
                "deaths": 0,
                }
            games[player.handle] = 0
        games[player.handle] += 1
        ret[player.handle]["frags"] += player.frags
        ret[player.handle]["deaths"] += player.deaths
    # Only count players who have played >= half the average number of games.
    # This avoids small numbers of games from skewing the values.
    gamemin = min([sum(games.values()) / max(1, len(games)) / 2,
                   max(games.values()) if games else 0])
    for h in ret:
        ret[h]['kdr'] = ret[h]['frags'] / max(1, ret[h]['deaths'])
    return [ret[h] for h in sorted([p for p in ret if games[p] >= gamemin],
                                   key=lambda p: ret[p]['kdr'],
                                   reverse=True)]


@cached(5 * 60)
def players_by_dpm(days):
    """
    Return a sorted list of players with and by dpm.
    """
    first_game = first_game_in_days(days)
    res_compiled = {}
    games = {}
    for player in (models.GamePlayer.query.join(models.Game)
                   .with_entities(models.GamePlayer.handle)
                   .filter(models.GamePlayer.game_id >= first_game)
                   .filter(models.GamePlayer.handle != "")
                   .filter(models.Game.normalweapons == 1)
                   .filter(models.Game.uniqueplayers > 1)):
        if player.handle not in games:
            games[player.handle] = 0
        games[player.handle] += 1
    for player in games.keys():
        d1, d2, timewielded = (
            models.GameWeapon.query.join(models.Game)
            .with_entities(db.func.sum(models.GameWeapon.damage1),
                           db.func.sum(models.GameWeapon.damage2),
                           db.func.sum(models.GameWeapon.timewielded))
            .filter(models.GameWeapon.playerhandle == player)
            .filter(models.GameWeapon.game_id >= first_game)
            .filter(models.Game.normalweapons == 1)
            .filter(~models.GameWeapon.weapon.in_(
                redeclipse.versions.default.notwielded
                ))).first()
        res_compiled[player] = {
            "handle": player,
            "dpm": (((d1 or 0) + (d2 or 0)) / (max(timewielded or 0, 1) / 60)),
            }
    # Only count players who have played >= half the average number of games.
    # This avoids small numbers of games from skewing the values.
    gamemin = min([sum(games.values()) / max(len(games), 1) / 2,
                   games and max(games.values()) or 0])
    return [res_compiled[p] for p in sorted([p for p in res_compiled
                                             if games[p] >= gamemin],
                                            key=lambda p:
                                                res_compiled[p]['dpm'],
                                            reverse=True)]


@cached(5 * 60)
def players_by_dpf(days):
    """
    Return a sorted list of players with and by dpf.
    """
    first_game = first_game_in_days(days)
    res_compiled = {}
    games = {}
    for player in (models.GamePlayer.query.join(models.Game)
                   .with_entities(models.GamePlayer.handle)
                   .filter(models.GamePlayer.game_id >= first_game)
                   .filter(models.GamePlayer.handle != "")
                   .filter(models.Game.normalweapons == 1)
                   .filter(models.Game.uniqueplayers > 1)):
        if player.handle not in games:
            games[player.handle] = 0
        games[player.handle] += 1
    for player in games.keys():
        d1, d2, f1, f2 = (
            models.GameWeapon.query.join(models.Game)
            .with_entities(db.func.sum(models.GameWeapon.damage1),
                           db.func.sum(models.GameWeapon.damage2),
                           db.func.sum(models.GameWeapon.frags1),
                           db.func.sum(models.GameWeapon.frags2))
            .filter(models.GameWeapon.playerhandle == player)
            .filter(models.GameWeapon.game_id >= first_game)
            .filter(models.Game.normalweapons == 1)
            .filter(~models.GameWeapon.weapon.in_(
                redeclipse.versions.default.notwielded
                ))).first()
        res_compiled[player] = {
            "handle": player,
            "dpf": (((d1 or 0) + (d2 or 0)) / max((f1 or 0) + (f2 or 0), 1)),
            }
    # Only count players who have played >= half the average number of games.
    # This avoids small numbers of games from skewing the values.
    gamemin = min([sum(games.values()) / max(len(games), 1) / 2,
                   games and max(games.values()) or 0])
    return [res_compiled[p] for p in sorted([p for p in res_compiled
                                             if games[p] >= gamemin],
                                            key=lambda p:
                                                res_compiled[p]['dpf'])]


@cached(10 * 60)
def player_weapons(days):
    """
    Return a sorted list of weapons and their best players with the most FPM.
    """
    first_game = first_game_in_days(days)
    res = (models.GameWeapon.query.join(models.Game)
           .filter(models.GameWeapon.game_id >= first_game)
           .filter(models.GameWeapon.playerhandle != "")
           .filter(models.Game.normalweapons == 1)
           .filter(models.GameWeapon.weapon.in_(
               redeclipse.versions.default.standardweaponlist))).all()
    weapons = {}
    totaltime = 0
    lentime = 0
    for weapon in redeclipse.versions.default.standardweaponlist:
        weapons[weapon] = {}
    for r in res:
        res_compiled = weapons[r.weapon]
        if r.playerhandle not in res_compiled:
            res_compiled[r.playerhandle] = {
                "handle": r.playerhandle,
                "damage": 0,
                "time": 0,
                }
        res_compiled[r.playerhandle]['damage'] += (r.damage1 + r.damage2)
        res_compiled[r.playerhandle]['time'] += r.time()
        totaltime += res_compiled[r.playerhandle]['time']
        lentime += 1
    for weapon in weapons:
        for h in weapons[weapon]:
            weapons[weapon][h]['dpm'] = (weapons[weapon][h]['damage'] /
                                         (max(weapons[weapon][h]['time'], 1) /
                                          60))
        weapons[weapon] = [weapons[weapon][p] for p in sorted(
                weapons[weapon], key=lambda p: weapons[weapon][p]['dpm'],
                reverse=True)]
    # Only select weapons that have been used for some time, no quick switches.
    mintime = max(totaltime, 1) / max(lentime, 1) / 2
    weapons_compiled = []
    for weapon in weapons:
        for player in weapons[weapon]:
            if player['time'] >= mintime:
                weapons_compiled.append({
                    "weapon": weapon,
                    "handle": player['handle'],
                    "dpm": player['dpm'],
                    })
    ret = []
    seen = []
    for entry in sorted(weapons_compiled,
                        key=lambda w: w['dpm'],
                        reverse=True):
        if entry['weapon'] in seen:
            continue
        seen.append(entry['weapon'])
        ret.append(entry)
    return ret
