from ..database import db_function
from ..dbmodels import Game
from . import versions


@db_function('re_mode')
def re_mode(game_id, mode):
    vclass = versions.get_game_version(game_id)

    if game_id in re_mode.cache:
        return re_mode.cache[game_id] == vclass.modes[mode]

    game = Game.query.filter(Game.id == game_id).first()
    re_mode.cache[game_id] = game.mode

    return game.mode == vclass.modes[mode]


re_mode.cache = {}


@db_function('re_mut')
def re_mut(game_id, mut):
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
