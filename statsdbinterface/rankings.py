import time
from .database import models, extmodels
from .database.core import db
from .function_cache import cached


def days_ago(days):
    return time.time() - (days * 60 * 60 * 24)


def weapon_sums(days):
    games = (models.Game.query
             .with_entities(models.Game.id)
             .filter(db.func.re_normal_weapons(models.Game.id))
             .filter(models.Game.time >= days_ago(days)))
    totalwielded = (models.GameWeapon.query
                    .with_entities(db.func.sum(
                        models.GameWeapon.timewielded))
                    .filter(models.GameWeapon.game_id.in_(
                        games
                        ))
                    .first()[0])
    weapons = extmodels.Weapon.all_from_games(games)
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


@cached(60)
def maps_by_games(days):
    """
    Return maps sorted by their number of games.
    Cache should be low, result could change quickly.
    """
    maps = [r[0] for r in models.Game.query
            .with_entities(models.Game.map)
            .filter(models.Game.time >= days_ago(days))]
    ret = []
    for map_ in set(maps):
        ret.append({
            "name": map_,
            "games": maps.count(map_),
            })
    return sorted(ret, key=lambda m: m['games'], reverse=True)
