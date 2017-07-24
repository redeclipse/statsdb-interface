from flask import current_app
from werkzeug.exceptions import NotFound
from .core import db
from .models import Game, GamePlayer, GameServer, GameWeapon
from .models import Mutator as GMut, Mode as GMode
from .modelutils import direct_to_dict, to_pagination
from .. import redeclipse
from .. function_cache import cached


class Player:
    @staticmethod
    def handle_list():
        # Return a list of all player handles in the database.
        ret = [r[0] for r in
               GamePlayer.query.with_entities(GamePlayer.handle).filter(
               GamePlayer.handle != None)
               .group_by(GamePlayer.handle)
               .order_by(GamePlayer.game_id.desc()).all()]  # noqa
        return ret

    @staticmethod
    def count():
        # Return the number of handles in the database.
        return GamePlayer.query.filter(GamePlayer.handle != None) \
                .group_by(GamePlayer.handle).count()  # noqa

    @staticmethod
    def get_or_404(handle):
        # Return a Player for <handle> if <handle> exists, otherwise 404.
        handles = Player.handle_list()
        if handle in handles:
            return Player(handle)
        else:
            raise NotFound

    @staticmethod
    def all(page=0, pagesize=None):
        # Return all players, with optional paging.
        filtered_handles = handles = Player.handle_list()
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_handles = handles[
                page * pagesize:page * pagesize + pagesize]
        return [Player(handle) for handle in filtered_handles]

    @classmethod
    def paginate(cls, page, per_page):
        return to_pagination(page, per_page, cls.all, cls.count)

    def __init__(self, handle):
        # Build a Player object from the database.
        self.handle = handle
        all_games = [r[0] for r in Game.query.with_entities(Game.id).all()]
        self.game_ids = [r[0] for r in GamePlayer.query.with_entities(
            GamePlayer.game_id).filter(GamePlayer.handle == self.handle).all()
            if r[0] in all_games]
        self.latest = GamePlayer.query.filter(
            GamePlayer.game_id == self.game_ids[-1],
            GamePlayer.handle == self.handle).first()
        self.first = GamePlayer.query.filter(
            GamePlayer.game_id == self.game_ids[0],
            GamePlayer.handle == self.handle).first()

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Player's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
               if pagesize is not None else self.game_ids)
        if not ids:
            return []
        return Game.query.filter(Game.id.in_(ids)).all()

    def recent_games(self, number):
        ids = reversed(self.game_ids[-number:])
        if not ids:
            return []
        return Game.query.filter(
            Game.id.in_(ids)).order_by(Game.id.desc()).all()

    def games_paginate(self, page, per_page):
        return to_pagination(page, per_page, self.games,
                             lambda: len(self.game_ids))

    def game_player(self, game_id):
        return GamePlayer.query.filter(
                GamePlayer.game_id == game_id).filter(
                GamePlayer.handle == self.handle).first()

    def last_games(self, number=0):
        if number == 0:
            return list(reversed(self.game_ids))
        else:
            return list(reversed(self.game_ids))[:number]

    @cached(5 * 60, 'handle')
    def dpm(self, games_ago):
        games = self.last_games(games_ago)
        d1, d2 = GameWeapon.query.with_entities(
            db.func.sum(GameWeapon.damage1),
            db.func.sum(GameWeapon.damage2)).filter(
                GameWeapon.game_id.in_(games),
                db.func.re_normal_weapons(GameWeapon.game_id),
                GameWeapon.playerhandle == self.handle
                ).first()
        time = GamePlayer.query.with_entities(
            db.func.sum(GamePlayer.timealive)).filter(
                GamePlayer.game_id.in_(games),
                db.func.re_normal_weapons(GamePlayer.game_id),
                GamePlayer.handle == self.handle
                ).first()[0]
        return ((d1 or 0) + (d2 or 0)) / (max(1, (time or 0)) / 60)

    @cached(5 * 60, 'handle')
    def fpm(self, games_ago):
        games = self.last_games(games_ago)
        time, frags = GamePlayer.query.with_entities(
            db.func.sum(GamePlayer.timealive),
            db.func.sum(GamePlayer.frags)).filter(
                GamePlayer.game_id.in_(games),
                db.func.re_normal_weapons(GamePlayer.game_id),
                GamePlayer.handle == self.handle
                ).first()
        return (frags or 0) / (max(1, (time or 0)) / 60)

    @cached(5 * 60, 'handle')
    def kdr(self, games_ago):
        games = self.last_games(games_ago)
        frags, deaths = GamePlayer.query.with_entities(
            db.func.sum(GamePlayer.frags),
            db.func.sum(GamePlayer.deaths)).filter(
                GamePlayer.game_id.in_(games),
                db.func.re_normal_weapons(GamePlayer.game_id),
                GamePlayer.handle == self.handle
                ).first()
        return (frags or 0) / max(1, deaths or 0)

    @cached(5 * 60, 'handle')
    def dfr(self, games_ago):
        games = self.last_games(games_ago)
        d1, d2 = GameWeapon.query.with_entities(
            db.func.sum(GameWeapon.damage1),
            db.func.sum(GameWeapon.damage2)).filter(
                GameWeapon.game_id.in_(games),
                db.func.re_normal_weapons(GameWeapon.game_id),
                GameWeapon.playerhandle == self.handle
                ).first()
        frags = GamePlayer.query.with_entities(
            db.func.sum(GamePlayer.frags)).filter(
                GamePlayer.game_id.in_(games),
                db.func.re_normal_weapons(GamePlayer.game_id),
                GamePlayer.handle == self.handle
                ).first()[0]
        return ((d1 or 0) + (d2 or 0)) / max(1, frags or 0)

    @cached(5 * 60, 'handle')
    def topmaps(self, games_ago):
        games = self.last_games(games_ago)
        maps = [r[0] for r in (Game.query
                               .with_entities(Game.map)
                               .filter(Game.id.in_(games))
                               )]
        ret = {}
        for map_ in set(maps):
            ret[map_] = maps.count(map_)
        return [{"name": m, "games": ret[m]}
                for m in sorted(sorted(ret),
                                key=lambda m: ret[m], reverse=True)]

    def weapons(self):
        ret = {}
        for weapon in redeclipse.versions.default.weaponlist:
            ret[weapon] = Weapon.from_player(weapon, self.handle)
        return ret

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
        ])


class Server:

    @staticmethod
    def handle_list():
        # Return a list of all server handles in the database.
        return [r[0] for r in
                GameServer.query.with_entities(GameServer.handle)
                .group_by(GameServer.handle)
                .order_by(GameServer.game_id.desc()).all()]

    @staticmethod
    def count():
        # Return the number of handles in the database.
        return GameServer.query.group_by(GameServer.handle).count()

    @staticmethod
    def get_or_404(handle):
        # Return a Server for <handle> if <handle> exists, otherwise 404.
        handles = Server.handle_list()
        if handle in handles:
            return Server(handle)
        else:
            raise NotFound

    @staticmethod
    def all(page=0, pagesize=None):
        # Return all servers, with optional paging.
        filtered_handles = handles = Server.handle_list()
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_handles = handles[
                page * pagesize:page * pagesize + pagesize]
        return [Server(handle) for handle in filtered_handles]

    @classmethod
    def paginate(cls, page, per_page):
        return to_pagination(page, per_page, cls.all, cls.count)

    def __init__(self, handle):
        # Build a Server object from the database.
        self.handle = handle
        all_games = [r[0] for r in Game.query.with_entities(Game.id).all()]
        self.game_ids = [r[0] for r in GameServer.query.with_entities(
            GameServer.game_id).filter(GameServer.handle == self.handle).all()
            if r[0] in all_games]
        self.latest = GameServer.query.filter(
            GameServer.game_id == self.game_ids[-1]).first()
        self.first = GameServer.query.filter(
            GameServer.game_id == self.game_ids[0]).first()

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Server's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
               if pagesize is not None else
               self.game_ids)
        if not ids:
            return []
        return Game.query.filter(Game.id.in_(ids)).all()

    def recent_games(self, number):
        ids = reversed(self.game_ids[-number:])
        if not ids:
            return []
        return Game.query.filter(
            Game.id.in_(ids)).order_by(Game.id.desc()).all()

    def games_paginate(self, page, per_page):
        return to_pagination(page, per_page, self.games,
                             lambda: len(self.game_ids))

    def to_dict(self):
        return direct_to_dict(self, [
            "handle", "game_ids"
        ], {
            "latest": self.latest.to_dict(),
            "first": self.first.to_dict(),
        })


class Map:
    @staticmethod
    def map_list(race=False):
        if race:
            return [r[0] for r in
                    db.session.query(db.distinct(Game.map))
                    .join(Game.mode).join(Game.mutators)
                    .filter(GMode.name == 'race')
                    .filter(GMut.name == 'timed')
                    .order_by(Game.id.desc())
                    .all()]
        # Return a list of all map names in the database.
        return [r[0] for r in
                Game.query.with_entities(Game.map).group_by(Game.map)
                .order_by(Game.id.desc()).all()]

    @staticmethod
    def count(race=False):
        # Return the number of maps in the database.
        if race:
            return db.session.query(db.distinct(Game.map)) \
                    .filter(GMode.name == 'race') \
                    .filter(GMut.name == 'timed') \
                    .count()
        return Game.query.with_entities(Game.map).group_by(Game.map).count()

    @staticmethod
    def get_or_404(name):
        # Return a Map for <name> if <name> exists, otherwise 404.
        names = Map.map_list()
        if name in names:
            return Map(name)
        else:
            raise NotFound

    @staticmethod
    def all(page=0, pagesize=None, race=False):
        # Return all m, with optional paging.
        filtered_names = names = Map.map_list(race)
        # If pagesize is specified, only return page <page> from the list.
        if pagesize is not None:
            filtered_names = names[
                page * pagesize:page * pagesize + pagesize]
        return [Map(name) for name in filtered_names]

    @classmethod
    def paginate(cls, page, per_page, race=False):
        return to_pagination(page, per_page,
                             lambda a, b: cls.all(a, b, race),
                             lambda: cls.count(True))

    def __init__(self, name):
        # Build a Map object from the database.
        self.name = name
        self.game_ids = [
            r[0] for r in
            Game.query.with_entities(Game.id).filter(
                Game.map == self.name
            ).all()
        ]
        self.latest = Game.query.filter(
            Game.id == self.game_ids[-1]).first()
        self.first = Game.query.filter(
            Game.id == self.game_ids[0]).first()
        self.gametime = Game.query.with_entities(
            db.func.sum(Game.timeplayed)).filter(
                Game.map == self.name
            ).first()[0]
        self.playertime = GamePlayer.query.with_entities(
            db.func.sum(GamePlayer.timeactive)).filter(
                GamePlayer.game_id.in_(self.game_ids)
            ).first()[0]

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Map's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
               if pagesize is not None else
               self.game_ids)
        if not ids:
            return []
        return Game.query.filter(Game.id.in_(ids)).all()

    def recent_games(self, number):
        ids = reversed(self.game_ids[-number:])
        if not ids:
            return []
        return Game.query.filter(
            Game.id.in_(ids)).order_by(Game.id.desc()).all()

    def games_paginate(self, page, per_page):
        return to_pagination(page, per_page, self.games,
                             lambda: len(self.game_ids))

    def topraces(self, endurance=False):
        # Return a dictionary of the top race times.
        games = db.session.query(Game.id.label('game_id'),
                                 Game.time) \
                .join(Game.mode).join(Game.mutators) \
                .filter(Game.map == self.name) \
                .filter(GMode.name == 'race') \
                .filter(GMut.name == 'timed') \
                .filter(True
                        if not endurance
                        else GMut.name == 'endurance') \
                .filter(~Game.mutators.any(name='freestyle')) \
                .subquery()
        scores = db.session.query(GamePlayer.game_id,
                                  GamePlayer.handle,
                                  GamePlayer.name,
                                  GamePlayer.score,
                                  games.c.time.label('when')) \
            .select_from(games) \
            .join(GamePlayer, games.c.game_id == GamePlayer.game_id) \
            .filter(GamePlayer.score > 0) \
            .group_by(GamePlayer.handle) \
            .having(db.func.min(GamePlayer.score)) \
            .order_by(GamePlayer.score.asc()) \
            .limit(current_app.config['API_HIGHSCORE_RESULTS']) \
            .all()

        return scores

    def to_dict(self):
        return direct_to_dict(self, [
            "name", "game_ids"
        ], {
            "topraces": self.topraces(),
        })


class Mode:
    @staticmethod
    def mode_list():
        return [mode for mode in
                redeclipse.versions.default.modes.keys()
                if mode not in ["demo", "edit"]]

    @staticmethod
    def count():
        return len(Mode.mode_list())

    @staticmethod
    def get_or_404(name):
        names = Mode.mode_list()
        if name in names:
            return Mode(name)
        else:
            raise NotFound

    @staticmethod
    def all():
        return [Mode(name) for name in Mode.mode_list()]

    def __init__(self, name):
        self.mode = GMode.query.filter_by(name=name).one()
        self.name = self.mode.name
        self.longname = self.mode.longname
        self.game_ids = [g.id for g in self.mode.games]

    def mode_str(self, short=False):
        return self.name if short else self.longname

    def games(self, page=0, pagesize=None):
        # Return full Game objects from Mode's game_ids.
        ids = (self.game_ids[page * pagesize:page * pagesize + pagesize]
               if pagesize is not None else
               self.game_ids)
        if not ids:
            return []
        return Game.query.filter(Game.id.in_(ids)).all()

    def recent_games(self, number):
        ids = reversed(self.game_ids[-number:])
        if not ids:
            return []
        return Game.query.filter(
            Game.id.in_(ids)).order_by(Game.id.desc()).all()

    def games_paginate(self, page, per_page):
        return to_pagination(page, per_page, self.games,
                             lambda: len(self.game_ids))

    def to_dict(self):
        return direct_to_dict(self, [
            "name", "game_ids"
        ])


class Mutator:

    @staticmethod
    def mutator_list():
        re = redeclipse.versions.default
        basemuts = re.basemuts.keys()
        gspmuts = []
        for mode in re.modes:
            modei = re.modes[mode]
            if modei in re.gspmuts:
                for mut in re.gspmuts[modei]:
                    gspmuts.append("%s-%s" % (mode, mut))
        return list(basemuts) + gspmuts

    @staticmethod
    def count():
        return len(Mutator.mutator_list())

    @staticmethod
    def get_or_404(name):
        names = Mutator.mutator_list()
        if name in names:
            return Mutator(name)
        else:
            raise NotFound

    @staticmethod
    def all():
        return [Mutator(name) for name in Mutator.mutator_list()]

    def __init__(self, name):
        mode, mut = name.split('-') if '-' in name else (None, name)
        self.mode = GMode.query.filter_by(name=mode).one() if mode else None
        self.mode_id = self.mode.id if self.mode else None
        self.mut = GMut.query.filter_by(name=mut, mode_id=self.mode_id).one()
        self.name = self.mut.link

    @property
    def game_ids(self):
        return [g.id for g in self.mut.games.all()]

    def games(self, page=0, pagesize=None):
        q = self.mut.games.order_by(Game.id.desc())
        if pagesize is not None:
            q.limit(pagesize).offset(page * pagesize)
        return q.all()

    def recent_games(self, number):
        ids = reversed(self.game_ids[-number:])
        if not ids:
            return []
        return Game.query.filter(
            Game.id.in_(ids)).order_by(Game.id.desc()).all()

    def games_paginate(self, page, per_page):
        return to_pagination(page, per_page, self.games,
                             lambda: len(self.game_ids))

    def to_dict(self):
        return direct_to_dict(self, [
            "name", "game_ids"
        ])


class Weapon:

    columns = ["timewielded", "timeloadout",
               "damage1", "frags1", "hits1", "flakhits1",
               "shots1", "flakshots1",
               "damage2", "frags2", "hits2", "flakhits2",
               "shots2", "flakshots2",
               ]

    @staticmethod
    def weapon_list():
        # Return a list of all default weapon names.
        return redeclipse.versions.default.weaponlist

    @staticmethod
    def count():
        # Return the number of default weapons.
        return len(Weapon.weapon_list())

    @staticmethod
    def finish_query(name, query):
        weapon = Weapon(name)
        qret = query.with_entities(*[
            db.func.sum(getattr(GameWeapon, c))
            for c in Weapon.columns]).first()
        for c in Weapon.columns:
            value = qret[Weapon.columns.index(c)]
            setattr(weapon, c, value if value is not None else 0)
        return weapon

    @staticmethod
    def from_player(weapon, player):
        return Weapon.finish_query(weapon, GameWeapon.query.filter(
            GameWeapon.weapon == weapon).filter(
                GameWeapon.playerhandle == player))

    @staticmethod
    def from_player_games(weapon, player, games):
        q = GameWeapon.query \
                .filter(GameWeapon.weapon == weapon) \
                .filter(GameWeapon.playerhandle == player) \
                .filter(GameWeapon.game_id.in_(games))
        return Weapon.finish_query(weapon, q)

    @staticmethod
    def from_game(weapon, game):
        return Weapon.finish_query(weapon, GameWeapon.query.filter(
            GameWeapon.weapon == weapon).filter(
                GameWeapon.game_id == game))

    @staticmethod
    def from_games(weapon, games):
        ret = Weapon.finish_query(weapon, GameWeapon.query.filter(
            GameWeapon.weapon == weapon).filter(
                GameWeapon.game_id.in_(games)))
        return ret

    @staticmethod
    def from_f(weapon, f):
        ret = Weapon.finish_query(
                weapon,
                GameWeapon.query.join(Game)
                          .filter(GameWeapon.weapon == weapon)
                          .filter(*f))
        return ret

    @staticmethod
    def from_game_player(weapon, game, player):
        return Weapon.finish_query(weapon, GameWeapon.query.filter(
            GameWeapon.weapon == weapon).filter(
                GameWeapon.game_id == game).filter(
                GameWeapon.playerhandle == player))

    @staticmethod
    def from_weapon(weapon):
        return Weapon.finish_query(weapon, GameWeapon.query.filter(
            GameWeapon.weapon == weapon))

    @staticmethod
    def get_or_404(name):
        names = Weapon.weapon_list()
        if name in names:
            return Weapon.from_weapon(name)
        else:
            raise NotFound

    @staticmethod
    def all():
        return [Weapon.from_weapon(n) for n in Weapon.weapon_list()]

    @staticmethod
    def all_from_games(games):
        return [Weapon.from_games(n, games) for n in Weapon.weapon_list()]

    @staticmethod
    def all_from_f(f):
        return [Weapon.from_f(n, f) for n in Weapon.weapon_list()]

    @staticmethod
    def all_from_game(game):
        return [Weapon.from_game(n, game) for n in Weapon.weapon_list()]

    @staticmethod
    def all_from_player_games(player, games):
        return [Weapon.from_player_games(n, player, games)
                for n in Weapon.weapon_list()]

    def __init__(self, name):
        self.name = name

    def is_not_wielded(self):
        re = redeclipse.versions.default
        return self.name in re.notwielded

    def time(self):
        if self.is_not_wielded():
            return self.timeloadout
        return self.timewielded

    def to_dict(self):
        return direct_to_dict(self, [
            "name"
        ] + Weapon.columns)
