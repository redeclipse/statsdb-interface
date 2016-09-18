# -*- coding: utf-8 -*-

from werkzeug.exceptions import NotFound
from .database import db
from .dbmodels import Game, GamePlayer, GameServer
from .modelutils import direct_to_dict
import config


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
        return Game.query.filter(Game.id.in_(ids)).all()

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
        # Build a Server object from the database.
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
        return Game.query.filter(Game.id.in_(ids)).all()

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
        ])


class Map:

    def map_list():
        # Return a list of all map names in the database.
        return [r[0] for r in
                Game.query.with_entities(Game.map).group_by(Game.map).all()]

    def count():
        # Return the number of maps in the database.
        return Game.query.with_entities(Game.map).group_by(Game.map).count()

    def get_or_404(name):
        # Return a Map for <name> if <name> exists, otherwise 404.
        handles = Map.map_list()
        if name in handles:
            return Map(name)
        else:
            raise NotFound

    def all(page=0, pagesize=None):
        # Return all m, with optional paging.
        filtered_names = names = Map.map_list()
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_names = names[
                page * pagesize:page * pagesize + pagesize]
        return [Map(name) for name in filtered_names]

    def __init__(self, name):
        # Build a Map object from the database.
        self.name = name
        self.game_ids = [r[0] for r in
            Game.query.with_entities(Game.id).filter(
                Game.map == self.name).all()]

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Map's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
                if pagesize is not None else
                self.game_ids)
        return Game.query.filter(Game.id.in_(ids)).all()

    def topraces(self):
        # Return a dictionary of the top race times.
        return [
            {
                "game_id": r[0],
                "handle": r[1],
                "name": r[2],
                "score": r[3],
            }
            for r in
            (
            GamePlayer.query
                # We only need some information.
                .with_entities(GamePlayer.game_id, GamePlayer.handle,
                    GamePlayer.name, GamePlayer.score)
                # Only games from this map.
                .filter(GamePlayer.game_id.in_(self.game_ids))
                # Only timed race.
                .filter(db.func.re_mode(GamePlayer.game_id, 'race'))
                .filter(db.func.re_mut(GamePlayer.game_id, 'timed'))
                # Scores of 0 indicate the race was never completed.
                .filter(GamePlayer.score > 0)
                # Get only the best score from each handle.
                .group_by(GamePlayer.handle)
                .having(db.func.min(GamePlayer.score))
                # Finally: order, limit, and fetch.
                .order_by(GamePlayer.score.asc())
                .limit(config.API_HIGHSCORE_RESULTS)
                .all()
            )
        ]

    def to_dict(self):
        return direct_to_dict(self, [
            "name", "game_ids"
        ], {
            "topraces": self.topraces(),
        })
