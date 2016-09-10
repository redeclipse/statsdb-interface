# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound
from statsdbinterface.dbmodels import Game, GamePlayer, GameServer
from statsdbinterface.modelutils import direct_to_dict


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
            GamePlayer.game_id).filter(GamePlayer.handle == self.handle).all()
            if Game.query.with_entities(Game.id).filter(
                Game.id == r[0]).scalar() is not None]

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Player's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
                if pagesize is not None else
                self.game_ids)
        ret = []
        for game_id in ids:
            ret.append(Game.query.filter(Game.id == game_id).first().to_dict())
        return ret

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
        ])


class Server:

    def handle_list():
        # Return a list of all server handles in the database.
        return [r[0] for r in
                GameServer.query.with_entities(GameServer.handle).filter(
                GameServer.handle != '').group_by(GameServer.handle).all()]

    def count():
        # Return the number of handles in the database.
        return GameServer.query.filter(
            GameServer.handle != '').group_by(GameServer.handle).count()

    def get_or_404(handle):
        # Return a Server for <handle> if <handle> exists, otherwise 404.
        handles = Server.handle_list()
        if handle in handles:
            return Server(handle)
        else:
            raise NotFound

    def all(page=0, pagesize=None):
        # Return all servers, with optional paging.
        filtered_handles = handles = Server.handle_list()
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_handles = handles[
                page * pagesize:page * pagesize + pagesize]
        return [Server(handle) for handle in filtered_handles]

    def __init__(self, handle):
        # Build a Player object from the database.
        self.handle = handle
        self.game_ids = [r[0] for r in GameServer.query.with_entities(
            GameServer.game_id).filter(GameServer.handle == self.handle).all()
            if Game.query.with_entities(Game.id).filter(
                Game.id == r[0]).scalar() is not None]

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Server's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
                if pagesize is not None else
                self.game_ids)
        ret = []
        for game_id in ids:
            ret.append(Game.query.filter(Game.id == game_id).first().to_dict())
        return ret

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
        ])
