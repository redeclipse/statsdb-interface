from ..database.core import db_function, db
from ..database.models import Game, GameServer
from . import versions


@db_function('re_normal_weapons')
def re_normal_weapons(game_id):
    re = versions.get_game_version(game_id)
    for mode in re.nonstandard_weapons['modes']:
        if re_mode(game_id, mode):
            return False
    for mutator in re.nonstandard_weapons['mutators']:
        if re_mut(game_id, mutator):
            return False
    return True


@db_function('re_mode')
def re_mode(game_id, mode):
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

    return (mut in vclass.mutslist(game.mode, game.mutators))


re_mut.cache = {}
re_mut.precache = {}
re_mode.lastprecache = 0


@db_function('re_ver')
def re_ver(version, vmin, vmax):
    vmin = versions.version_str_to_tuple(vmin)
    vmax = versions.version_str_to_tuple(vmax)
    v = versions.version_str_to_tuple(version)

    return v >= vmin and v <= vmax


def build_precache():
    """
    Build a precache of games before the current run.
    """
    re_mut.lastprecache = re_mode.lastprecache = Game.query.with_entities(
        db.func.max(Game.id)).first()[0]
    for vclass in versions.registry:
        for mode in vclass.modes:
            if mode not in re_mode.precache:
                re_mode.precache[mode] = []
            re_mode.precache[mode] += [
                r[0] for r in
                Game.query.with_entities(Game.id)
                .join(Game.server)
                .filter(db.func.re_ver(GameServer.version, vclass.startstr,
                                       vclass.endstr))
                .filter(Game.mode == vclass.modes[mode]).all()
            ]
        for mut in vclass.mutators:
            if mut not in re_mut.precache:
                re_mut.precache[mut] = []
            re_mut.precache[mut] += [
                r[0] for r in
                Game.query.with_entities(Game.id)
                .join(Game.server)
                .filter(db.func.re_ver(GameServer.version, vclass.startstr,
                                       vclass.endstr))
                .filter(Game.mutators.op('&')(vclass.mutators[mut])).all()
            ]
