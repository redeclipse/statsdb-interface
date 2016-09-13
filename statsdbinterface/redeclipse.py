# -*- coding: utf-8 -*-
from statsdbinterface.database import db_function


@db_function('re_mode')
def re_mode(game_id, mode):
    return True


@db_function('re_mut')
def re_mut(game_id, mut):
    return True
