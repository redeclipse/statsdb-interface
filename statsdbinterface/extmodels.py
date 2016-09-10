# -*- coding: utf-8 -*-
from statsdbinterface.dbmodels import Game, GamePlayer
from statsdbinterface.modelutils import direct_to_dict
from werkzeug.exceptions import NotFound


class Player:

    def handle_list():
        # Return a list of all player handles in the database.
        return [r[0] for r in
            GamePlayer.query.with_entities(GamePlayer.handle).filter(
                GamePlayer.handle != '').group_by(GamePlayer.handle).all()]

    def count():
        # Return the number of handles in the database.
        return GamePlayer.query.filter(
            GamePlayer.handle != '').group_by(GamePlayer.handle).count()

    def get_or_404(handle):
        # Return a Player for <handle> if <handle> exists, otherwise 404.
        handles = Player.handle_list()
        if handle in handles:
            return Player(handle)
        else:
            raise NotFound

    def all(page=0, pagesize=None):
        # Return all players, with optional paging.
        filtered_handles = handles = Player.handle_list()
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_handles = handles[
                page * pagesize:page * pagesize + pagesize]
        return [Player(handle) for handle in filtered_handles]

    def __init__(self, handle):
        # Build a Player object from the database.
        self.handle = handle
        self.game_ids = [r[0] for r in GamePlayer.query.with_entities(
            GamePlayer.game_id).filter(GamePlayer.handle == self.handle).all()]

    def games(self):
        # Return full Game objects from Player's game_ids.
        ret = []
        for game_id in self.game_ids:
            ret.append(Game.query.filter(Game.id == game_id).first().to_dict())
        return ret

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
            ])
