from ..database.core import db_function, db
from . import versions


@db_function('re_normal_weapons')
def re_normal_weapons(game_id):
    if game_id in re_normal_weapons.cache:
        return re_normal_weapons.cache[game_id]
    re = versions.get_game_version(game_id)
    ret = True
    for mode in re.nonstandard_weapons['modes']:
        if re_mode(game_id, mode):
            ret = False
            break
    for mutator in re.nonstandard_weapons['mutators']:
        if re_mut(game_id, mutator):
            ret = False
            break
    re_normal_weapons.cache[game_id] = ret
re_normal_weapons.cache = {}


@db_function('re_mode')
def re_mode(game_id, mode):
    from ..database.models import Game
    if mode in re_mode.precache and game_id <= re_mode.lastprecache:
        return game_id in re_mode.precache[mode]

    vclass = versions.get_game_version(game_id)

    if game_id in re_mode.cache:
        return re_mode.cache[game_id] == vclass.modes[mode]

    game = Game.query.filter(Game.id == game_id).first()
    re_mode.cache[game_id] = game.mode

    return game.mode == vclass.modes[mode]


re_mode.cache = {}
re_mode.precache = {}
re_mode.lastprecache = 0


@db_function('re_mut')
def re_mut(game_id, mut):
    from ..database.models import Game
    if mut in re_mut.precache and game_id <= re_mut.lastprecache:
        return game_id in re_mut.precache[mut]

    vclass = versions.get_game_version(game_id)

    if game_id in re_mut.cache:
        return mut in vclass.mutslist(
            re_mut.cache[game_id][0],
            re_mut.cache[game_id][1]
        )

    game = Game.query.filter(Game.id == game_id).first()

    re_mut.cache[game_id] = (game.mode, game.mutators)

    return mut in vclass.mutslist(game.mode, game.mutators)


re_mut.cache = {}
re_mut.precache = {}
re_mode.lastprecache = 0


@db_function('re_ver')
def re_ver(version, vclass):
    return type(versions.get_version_class(version)).__name__ == vclass


def build_precache():
    """
    Build a precache of games before the current run.
    """
    from ..database.models import Game, GameServer
    re_mut.lastprecache = re_mode.lastprecache = Game.query.with_entities(
        db.func.max(Game.id)).first()[0]
    for vclass in versions.registry:
        for mode in vclass.modes:
            if mode not in re_mode.precache:
                re_mode.precache[mode] = set()
            re_mode.precache[mode].update(
                r[0] for r in
                Game.query.with_entities(Game.id)
                .join(Game.server)
                .filter(db.func.re_ver(GameServer.version,
                                       type(vclass).__name__))
                .filter(Game.mode == vclass.modes[mode]).all()
            )
        for mut in vclass.mutators:
            if mut not in re_mut.precache:
                re_mut.precache[mut] = set()
            re_mut.precache[mut].update(
                r[0] for r in
                Game.query.with_entities(Game.id)
                .join(Game.server)
                .filter(db.func.re_ver(GameServer.version,
                                       type(vclass).__name__))
                .filter(Game.mutators.op('&')(vclass.mutators[mut])).all()
                )
