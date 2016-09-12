# -*- coding: utf-8 -*-
from statsdbinterface.database import db_function


@db_function('re_mode', 2)
def re_mode(game_id, mode):
    return True
