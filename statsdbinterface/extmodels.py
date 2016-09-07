# -*- coding: utf-8 -*-
from statsdbinterface.dbmodels import GamePlayer


class Player:

    def handle_list():
        # Return a list of all player handles in the database.
        return [r[0] for r in
            GamePlayer.query.with_entities(GamePlayer.handle).filter(
                GamePlayer.handle != '').group_by(GamePlayer.handle).all()]
