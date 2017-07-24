from sqlalchemy import and_, CheckConstraint, UniqueConstraint
from .core import db
from .modelutils import direct_to_dict, list_to_id_dict
from .. import redeclipse


class GameBombing(db.Model):
    __tablename__ = "game_bombings"

    rowid = db.Column(db.Integer, primary_key=True)
    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'))
    game = db.relationship('Game',
                           backref=db.backref('bombings', lazy='dynamic'))
    player = db.Column(db.Integer)
    playerhandle = db.Column(db.Text)
    bombing = db.Column(db.Integer)
    bombed = db.Column(db.Integer)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle",
            "bombing", "bombed"
        ])


class GameCapture(db.Model):
    __tablename__ = "game_captures"

    rowid = db.Column(db.Integer, primary_key=True)
    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'))
    game = db.relationship('Game',
                           backref=db.backref('captures', lazy='dynamic'))
    player = db.Column(db.Integer)
    playerhandle = db.Column(db.Text)
    capturing = db.Column(db.Integer)
    captured = db.Column(db.Integer)

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
    game = db.relationship('Game',
                           backref=db.backref('teams', lazy='dynamic'))
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
    game = db.relationship('Game',
                           backref=db.backref('ffarounds', lazy='dynamic'))
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
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True, nullable=False)
    game = db.relationship('Game',
                           backref=db.backref('weapons', lazy='dynamic'))
    player = db.Column(db.Integer, primary_key=True, nullable=False)
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

    def is_not_wielded(self):
        re = redeclipse.versions.default
        return self.weapon in re.notwielded

    def time(self):
        if self.is_not_wielded():
            return self.timeloadout
        return self.timewielded

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "player", "playerhandle", "weapon",
            "timewielded", "timeloadout",
            "damage1", "frags1", "hits1", "flakhits1", "shots1", "flakshots1",
            "damage2", "frags2", "hits2", "flakhits2", "shots2", "flakshots2",
        ])


game_mutators_table = db.Table(
    'game_mutators', db.Model.metadata,
    db.Column('game_id', db.Integer, db.ForeignKey('games.id')),
    db.Column('mutator_id', db.Integer, db.ForeignKey('mutators.id')),
    UniqueConstraint('game_id', 'mutator_id'))


class Game(db.Model):
    __tablename__ = 'games'
    __table_args__ = (CheckConstraint("map <> ''"),)

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    time = db.Column(db.Integer, nullable=False)
    map = db.Column(db.Text, nullable=False, index=True)
    mode_id = db.Column(db.Integer, db.ForeignKey('modes.id'),
                        nullable=False, index=True)
    mode = db.relationship('Mode', back_populates='games', lazy=False,
                           innerjoin=True)
    timeplayed = db.Column(db.Integer, nullable=False)
    uniqueplayers = db.Column(db.Integer, nullable=False)
    normalweapons = db.Column(db.Integer, nullable=False, index=True)
    mutators = db.relationship('Mutator', secondary=game_mutators_table,
                               back_populates='games', lazy=False)
    server = db.relationship('GameServer', back_populates='game',
                             uselist=False, lazy=False, innerjoin=True)
    players = db.relationship('GamePlayer', back_populates='game')

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

    def full_weapons(self):
        from .extmodels import Weapon
        ret = {}
        for weapon in redeclipse.versions.default.weaponlist:
            ret[weapon] = Weapon.from_game(weapon, self.id)
        return ret

    def re(self):
        return redeclipse.versions.get_game_version(self.id)

    def is_timed(self):
        return (self.mode.name == 'race' and
                'timed' in set(m.name for m in self.mutators))

    def is_peaceful(self):
        return (self.mode.name == 'race' and
                'gauntlet' not in set(m.name for m in self.mutators))

    def mode_str(self, short=False):
        return self.mode.name if short else self.mode.longname

    def mutator_list(self, maxlong=0):
        name = 'shortname' if len(self.mutators) > maxlong else 'name'
        return [getattr(m, name) for m in self.mutators]

    def ordered_players(self):
        players = db.session.query(GamePlayer) \
                .filter(GamePlayer.game_id == self.id)
        if self.is_timed():
            return (players.order_by(
                GamePlayer.score.asc()).filter(GamePlayer.score != 0).all() +
                players.filter(GamePlayer.score == 0).all())
        else:
            return players.order_by(
                GamePlayer.score.desc(), GamePlayer.frags.desc(),
                GamePlayer.deaths.asc()).all()

    def ordered_teams(self):
        if self.is_timed():
            return (self.teams.order_by(
                GameTeam.score.asc()).filter(GamePlayer.score != 0).all() +
                self.teams.filter(GameTeam.score == 0).all())
        else:
            return self.teams.order_by(
                GameTeam.score.desc(), GameTeam.team.asc()).all()

    def player_by_wid(self, wid):
        for player in self.players:
            if player.wid == wid:
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
                "mutators": [m.name for m in self.mutators],
                "teams": list_to_id_dict([t.to_dict() for t in self.teams],
                                         "team"),
                "players": list_to_id_dict([p.to_dict() for p in self.players],
                                           "wid"),
                "ffarounds": self.combined_ffarounds(),
                "server": self.server.to_dict(),
            }
        )


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

    def __repr__(self):
        return '<GamePlayer %d from %d (%s [%s])>' % (
            self.wid, self.game_id, self.name, self.handle)

    def bombings(self):
        return [b.to_dict() for b in GameBombing.query.filter(
            and_(GameBombing.game_id == self.game_id,
                GameBombing.player == self.wid)).all()]

    def captures(self):
        return [b.to_dict() for b in GameCapture.query.filter(
            and_(GameCapture.game_id == self.game_id,
                GameCapture.player == self.wid)).all()]

    def damage(self):
        res = GameWeapon.query.with_entities(
            db.func.sum(GameWeapon.damage1), db.func.sum(GameWeapon.damage2)
            ).filter(GameWeapon.game_id == self.game_id).filter(
                GameWeapon.player == self.wid).all()
        return (res[0][0] or 0) + (res[0][1] or 0)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "name", "handle",
            "score", "timealive", "frags", "deaths", "wid", "timeactive"
        ], {
            "bombings": self.bombings(),
            "captures": self.captures(),
        })


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


class Mutator(db.Model):
    __tablename__ = 'mutators'
    __table_args__ = (CheckConstraint("name <> ''"),
                      CheckConstraint("shortname <> ''"),)

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    mode_id = db.Column(db.Integer, db.ForeignKey('modes.id'))
    mode = db.relationship('Mode', lazy=False)
    name = db.Column(db.Text, unique=True, nullable=False)
    shortname = db.Column(db.Text, nullable=False)
    games = db.relationship('Game', secondary=game_mutators_table,
                            back_populates='mutators', lazy='dynamic')

    @property
    def longname(self):
        return self.name

    @property
    def link(self):
        pref = self.mode.name + '-' if self.mode else ''
        return pref + self.name


class Mode(db.Model):
    __tablename__ = 'modes'
    __table_args__ = (CheckConstraint("name <> ''"),
                      CheckConstraint("longname <> ''"))

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.Integer, unique=True, nullable=False)
    longname = db.Column(db.Integer, unique=True, nullable=False)
    games = db.relationship('Game', back_populates='mode', lazy='dynamic')
