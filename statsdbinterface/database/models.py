from sqlalchemy import and_, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property, Comparator
from .core import db
from .modelutils import direct_to_dict, list_to_id_dict
from ..utils import classproperty, days_ago
from ..function_cache import cached


class GameBombing(db.Model):
    __tablename__ = "game_bombings"

    rowid = db.Column(db.Integer, primary_key=True)
    game_id = db.Column('game', db.Integer, db.ForeignKey('games.id'))
    game = db.relationship('Game', back_populates='bombings')
    player = db.Column(db.Integer)
    playerhandle = db.Column(db.Text)
    bombing = db.Column(db.Integer, db.ForeignKey('game_teams.team'))
    bombing_team = db.relationship(
        'GameTeam',
        primaryjoin='and_(GameTeam.game_id == GameBombing.game_id,'
                         'GameTeam.team == GameBombing.bombing)',
        viewonly=True)  # noqa
    bombed = db.Column(db.Integer, db.ForeignKey('game_teams.team'))
    bombed_team = db.relationship(
        'GameTeam',
        primaryjoin='and_(GameTeam.game_id == GameBombing.game_id,'
                         'GameTeam.team == GameBombing.bombed)',
        viewonly=True)  # noqa

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle",
            "bombing", "bombed"
        ])


class GameCapture(db.Model):
    __tablename__ = "game_captures"

    rowid = db.Column(db.Integer, primary_key=True)
    game_id = db.Column('game', db.Integer, db.ForeignKey('games.id'),
                        db.ForeignKey('game_players.game'))
    game = db.relationship('Game', back_populates='captures')
    player = db.Column(db.Integer, db.ForeignKey('game_players.wid'))
    playerhandle = db.Column(db.Text)
    capturing = db.Column(db.Integer, db.ForeignKey('game_teams.team'))
    capturing_team = db.relationship(
        'GameTeam',
        primaryjoin='and_(GameTeam.game_id == GameCapture.game_id,'
                         'GameTeam.team == GameCapture.capturing)',
        viewonly=True)  # noqa
    captured = db.Column(db.Integer, db.ForeignKey('game_teams.team'))
    captured_team = db.relationship(
        'GameTeam',
        primaryjoin='and_(GameTeam.game_id == GameCapture.game_id,'
                         'GameTeam.team == GameCapture.captured)',
        viewonly=True) # noqa

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle",
            "capturing", "captured"
        ])


class GameTeam(db.Model):
    __tablename__ = "game_teams"

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True)
    game = db.relationship('Game', back_populates='teams')
    team = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer)
    name = db.Column(db.Text)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "team", "score", "name"
        ])


class GameFFARound(db.Model):
    __tablename__ = "game_ffarounds"

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True)
    game = db.relationship('Game', back_populates='ffarounds')
    player = db.Column(db.Integer, primary_key=True)
    playerhandle = db.Column(db.Text)
    round = db.Column(db.Integer, primary_key=True)
    winner = db.Column(db.Boolean)

    def __repr__(self):
        return '<GameFFARound %d from %d (%d)>' % (self.round,
                                                   self.game_id, self.player)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle", "round", "winner"
        ])


class GameWeapon(db.Model):
    __tablename__ = "game_weapons"
    __table_args__ = (
        CheckConstraint("timewielded > 0 OR timeloadout > 0"),
        CheckConstraint("playerhandle <> ''"),
        CheckConstraint("weapon IN ('melee', 'pistol', 'sword', \
                'shotgun', 'smg', 'flamer', 'plasma', 'zapper', \
                'rifle', 'grenade', 'mine', 'rocket', 'claw')"),)

    game_id = db.Column('game',
                        db.Integer,
                        db.ForeignKey('games.id'),
                        db.ForeignKey('game_players.game'),
                        primary_key=True, nullable=False)
    game = db.relationship('Game',
                           backref=db.backref('weapons', lazy='dynamic'))
    player = db.Column(db.Integer, db.ForeignKey('game_players.wid'),
                       primary_key=True, nullable=False)
    playerhandle = db.Column(db.Text)
    weapon = db.Column(db.Text, primary_key=True, nullable=False)

    timewielded = db.Column(db.Integer, nullable=False)
    timeloadout = db.Column(db.Integer, nullable=False)

    damage1 = db.Column(db.Integer, nullable=False)
    frags1 = db.Column(db.Integer, nullable=False)
    hits1 = db.Column(db.Integer, nullable=False)
    flakhits1 = db.Column(db.Integer, nullable=False)
    shots1 = db.Column(db.Integer, nullable=False)
    flakshots1 = db.Column(db.Integer, nullable=False)

    damage2 = db.Column(db.Integer, nullable=False)
    frags2 = db.Column(db.Integer, nullable=False)
    hits2 = db.Column(db.Integer, nullable=False)
    flakhits2 = db.Column(db.Integer, nullable=False)
    shots2 = db.Column(db.Integer, nullable=False)
    flakshots2 = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<GameWeapon %s from %d (%d)>' % (self.weapon,
                                                 self.game_id, self.player)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle", "weapon",
            "timewielded", "timeloadout",
            "damage1", "frags1", "hits1", "flakhits1", "shots1", "flakshots1",
            "damage2", "frags2", "hits2", "flakhits2", "shots2", "flakshots2",
        ])


class GameMutator(db.Model):
    __tablename__ = 'game_mutators'

    rowid = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    mutator_id = db.Column(db.Integer, db.ForeignKey('mutators.id'))


class ModeComparator(Comparator):

    def __eq__(self, other):
        return self.mode_id == other.mode_id

    def in_(self, xs):
        return self.__clause_element__().mode_id.in_([x.id for x in xs])


class ModeAttr:

    @hybrid_property
    def mode(self):
        return Mode.get(self.mode_id)

    @mode.expression
    def mode(cls):
        return cls.mode_id

    @mode.comparator
    def mode(cls):
        return ModeComparator(cls)


class Game(db.Model, ModeAttr):
    __tablename__ = 'games'
    __table_args__ = (CheckConstraint("map <> ''"),)

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    map = db.Column(db.Text, nullable=False, index=True)
    mode_id = db.Column(db.Integer, db.ForeignKey('modes.id'),
                        nullable=False, index=True)

    timeplayed = db.Column(db.Integer, nullable=False)
    uniqueplayers = db.Column(db.Integer, nullable=False)
    normalweapons = db.Column(db.Integer, nullable=False, index=True)
    mutator_ids = db.relationship('GameMutator', lazy=False)
    server = db.relationship('GameServer', back_populates='game',
                             uselist=False, lazy=False, innerjoin=True)
    players = db.relationship('GamePlayer', back_populates='game')
    teams = db.relationship('GameTeam', back_populates='game')
    bombings = db.relationship('GameBombing', back_populates='game')
    captures = db.relationship('GameCapture', back_populates='game')
    ffarounds = db.relationship('GameFFARound', back_populates='game',
                                order_by=GameFFARound.round)

    @hybrid_property
    def mutators(self):
        muts = [Mutator.get(gm.mutator_id) for gm in self.mutator_ids]
        muts.sort(key=lambda m: Mutator.mutator_order[m.name])
        return muts

    def __repr__(self):
        return '<Game %d>' % self.id

    def combined_ffarounds(self):
        # Combine the various game_ffarounds entries into a single list.
        ffarounds = {}
        for ffaround in self.ffarounds:
            index = ffaround.round
            if index not in ffarounds:
                ffarounds[index] = {
                    "round": index,
                    "winner": None,
                    "players": [],
                }
            if ffaround.winner:
                ffarounds[index]["winner"] = ffaround.player
            ffarounds[index]["players"].append(ffaround.player)
        return ffarounds

    def is_timed(self):
        return (self.mode.name == 'race' and
                'timed' in set(m.name for m in self.mutators))

    def is_peaceful(self):
        return (self.mode.name == 'race' and
                'gauntlet' not in set(m.name for m in self.mutators))

    def mode_str(self, short=False):
        return self.mode.name if short else self.mode.longname

    def ordered_players(self):
        def timed_key(p):
            return p.score if p.score > 0 else float('inf')

        def nontimed_key(p):
            return (-p.score, -p.frags, p.deaths)

        key = timed_key if self.is_timed() else nontimed_key
        return sorted(self.players, key=key)

    def ordered_teams(self):
        if self.is_timed():
            inf = float('inf')
            return sorted(self.teams, key=lambda t: t.score or inf)
        else:
            return sorted(self.teams, key=lambda t: t.score or 0)

    def player_by_wid(self, wid):
        for player in self.players:
            if player.wid == wid:
                return player
        return None

    def player(self, handle):
        for player in self.players:
            if player.handle == handle:
                return player
        return None

    def to_dict(self):
        return direct_to_dict(
            self,
            [
                "id", "time", "map",
                "timeplayed", "uniqueplayers",
                "normalweapons"
            ],
            {
                "mode": self.mode.name,
                "server": self.server.to_dict(),
                "mutators": [m.name for m in self.mutators],
                "teams": [t.to_dict() for t in self.teams],
                "players": [p.to_dict() for p in self.players],
                "ffarounds": [f.to_dict() for f in self.ffarounds],
                "captures": [c.to_dict() for c in self.captures],
                "bombings": [b.to_dict() for b in self.bombings],
            }
        )

    @classproperty
    def list(cls):
        return Game.query.options(db.joinedload(Game.players)) \
                .order_by(Game.id.desc())


    @staticmethod
    @cached(60)
    def first_in_days(days):
        last_game_before = db.session \
            .query(db.func.max(Game.id)) \
            .filter(Game.time < days_ago(days)) \
            .scalar()
        return (last_game_before or 0) + 1


class GamePlayer(db.Model):
    __tablename__ = 'game_players'
    __table__args__ = (CheckConstraint("name <> ''"),
                       CheckConstraint("handle <> ''"),
                       UniqueConstraint('game', 'wid'),
                       UniqueConstraint('game', 'handle'),)

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True, nullable=False, index=True)
    game = db.relationship('Game', back_populates='players')
    name = db.Column(db.Text, nullable=False)
    handle = db.Column(db.Text, index=True)
    score = db.Column(db.Integer, nullable=False)
    timealive = db.Column(db.Integer, nullable=False)
    frags = db.Column(db.Integer, nullable=False)
    deaths = db.Column(db.Integer, nullable=False)
    wid = db.Column(db.Integer, primary_key=True, nullable=False)
    timeactive = db.Column(db.Integer, nullable=False)
    weapons = db.relationship('GameWeapon',
        primaryjoin='and_(GamePlayer.game_id == GameWeapon.game_id, '
                         'GamePlayer.wid == GameWeapon.player)',
        viewonly=True)  # noqa
    captures = db.relationship('GameCapture',
        primaryjoin='and_(GamePlayer.game_id == GameCapture.game_id, '
                         'GamePlayer.wid == GameCapture.player)',
        viewonly=True)  # noqa

    def __repr__(self):
        return '<GamePlayer %d from %d (%s [%s])>' % (
            self.wid, self.game_id, self.name, self.handle)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "name", "handle",
            "score", "timealive", "frags", "deaths", "wid", "timeactive"
        ], {})


class GameServer(db.Model):
    __tablename__ = 'game_servers'
    __table_args__ = (CheckConstraint("handle <> ''"),)

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True, nullable=False)
    game = db.relationship('Game', back_populates='server')
    handle = db.Column(db.Text, nullable=False, index=True)
    flags = db.Column(db.Text, nullable=False)
    desc = db.Column(db.Text, nullable=False)
    version = db.Column(db.Text, nullable=False)
    host = db.Column(db.Text, nullable=False)
    port = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<GameServer %s from %d)>' % (self.handle, self.game_id)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "handle", "flags", "desc", "version", "host", "port"
        ])


class Mutator(db.Model, ModeAttr):
    __tablename__ = 'mutators'
    __table_args__ = (CheckConstraint("name <> ''"),
                      CheckConstraint("shortname <> ''"),)

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    mode_id = db.Column(db.Integer, db.ForeignKey('modes.id'))
    name = db.Column(db.Text, unique=True, nullable=False)
    shortname = db.Column(db.Text, nullable=False)
    games = db.relationship('Game', secondary='game_mutators',
                            lazy='dynamic')

    @property
    def longname(self):
        return self.name

    @property
    def link(self):
        pref = self.mode.name + '-' if self.mode else ''
        return pref + self.name

    _mutators = {}
    mutator_order = [
        'multi', 'ffa', 'coop', 'insta', 'medieval', 'kaboom', 'duel',
        'survivor', 'classic', 'onslaught', 'freestyle', 'vampire',
        'resize', 'hard', 'basic', 'hold', 'basket', 'attack', 'quick',
        'defend', 'protect', 'king', 'gladiator', 'oldschool', 'timed',
        'endurance', 'gauntlet']

    @classmethod
    def init(cls):
        for mut in Mutator.query.all():
            cls._mutators[mut.id] = mut
            setattr(cls, mut.link.replace('-', '_'), mut)

        order = {}
        for i, mut in enumerate(cls.mutator_order):
            order[mut] = i
        cls.mutator_order = order

    @classmethod
    def get(cls, id):
        return cls._mutators.get(id, None)

    @classmethod
    def by_link(cls, link):
        return getattr(cls, link.replace('-', '_'), None)


class Mode(db.Model):
    __tablename__ = 'modes'
    __table_args__ = (CheckConstraint("name <> ''"),
                      CheckConstraint("longname <> ''"))

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.Integer, unique=True, nullable=False)
    longname = db.Column(db.Integer, unique=True, nullable=False)
    games = db.relationship('Game', lazy='dynamic')

    _modes = {}

    @classmethod
    def init(cls):
        for mode in Mode.query.all():
            cls._modes[mode.id] = mode
            setattr(cls, mode.name, mode)

    @classmethod
    def get(cls, id):
        return cls._modes.get(id, None)
