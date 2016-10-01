from sqlalchemy import and_
from .database import db
from .modelutils import direct_to_dict, list_to_id_dict
from . import redeclipse


class GameBombing(db.Model):
    __tablename__ = "game_bombings"

    rowid = db.Column(db.Integer, primary_key=True)
    game = db.Column(db.Integer)
    player = db.Column(db.Integer)
    playerhandle = db.Column(db.Text)
    bombing = db.Column(db.Integer)
    bombed = db.Column(db.Integer)

    def to_dict(self):
        return direct_to_dict(self, [
            "game", "player", "playerhandle",
            "bombing", "bombed"
        ])


class GameCapture(db.Model):
    __tablename__ = "game_captures"

    rowid = db.Column(db.Integer, primary_key=True)
    game = db.Column(db.Integer)
    player = db.Column(db.Integer)
    playerhandle = db.Column(db.Text)
    capturing = db.Column(db.Integer)
    captured = db.Column(db.Integer)

    def to_dict(self):
        return direct_to_dict(self, [
            "game", "player", "playerhandle",
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

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True)
    game = db.relationship('Game',
                           backref=db.backref('weapons', lazy='dynamic'))
    player = db.Column(db.Integer, primary_key=True)
    playerhandle = db.Column(db.Text)
    weapon = db.Column(db.Text, primary_key=True)

    timewielded = db.Column(db.Integer)
    timeloadout = db.Column(db.Integer)

    damage1 = db.Column(db.Integer)
    frags1 = db.Column(db.Integer)
    hits1 = db.Column(db.Integer)
    flakhits1 = db.Column(db.Integer)
    shots1 = db.Column(db.Integer)
    flakshots1 = db.Column(db.Integer)

    damage2 = db.Column(db.Integer)
    frags2 = db.Column(db.Integer)
    hits2 = db.Column(db.Integer)
    flakhits2 = db.Column(db.Integer)
    shots2 = db.Column(db.Integer)
    flakshots2 = db.Column(db.Integer)

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


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Integer)
    map = db.Column(db.Text)
    mode = db.Column(db.Integer)
    mutators = db.Column(db.Integer)
    timeplayed = db.Column(db.Integer)
    uniqueplayers = db.Column(db.Integer)
    usetotals = db.Column(db.Integer)

    def __repr__(self):
        return '<Game %d>' % (self.id)

    def combined_ffarounds(self):
        # Combine the various game_ffarounds entries into a single list.
        ffarounds = {}
        for ffaround in self.ffarounds:
            index = ffaround.round
            if index not in ffarounds:
                ffarounds[index] = {
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
        return (self.mode == self.re().modes['race'] and
                'timed' in self.re().mutslist(self.mode, self.mutators))

    def is_peaceful(self):
        return (self.mode == self.re().modes['race'] and
                'gauntlet' not in self.re().mutslist(self.mode, self.mutators))

    def mode_str(self, short=False):
        return (self.re().cmodestr[self.mode] if short else
                self.re().modestr[self.mode])

    def mutator_list(self, maxlong=0):
        return self.re().mutslist(self.mode, self.mutators,
                                  (maxlong and len(self.re().mutslist(
                                   self.mode, self.mutators)) > maxlong))

    def ordered_players(self):
        if self.is_timed():
            return (self.players.order_by(
                GamePlayer.score.asc()).filter(GamePlayer.score != 0).all() +
                self.players.filter(GamePlayer.score == 0).all())
        else:
            return self.players.order_by(
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

    def to_dict(self):
        return direct_to_dict(
            self,
            [
                "id", "time",
                "map", "mode", "mutators",
                "timeplayed", "uniqueplayers",
                "usetotals"
            ],
            {
                "teams": list_to_id_dict([t.to_dict() for t in self.teams],
                                         "team"),
                "players": list_to_id_dict([p.to_dict() for p in self.players],
                                           "wid"),
                "ffarounds": self.combined_ffarounds(),
                "server": self.server.first().to_dict(),
            }
        )


class GamePlayer(db.Model):
    __tablename__ = 'game_players'

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True)
    game = db.relationship('Game',
                           backref=db.backref('players', lazy='dynamic'))
    name = db.Column(db.Text)
    handle = db.Column(db.Text)
    score = db.Column(db.Integer)
    timealive = db.Column(db.Integer)
    frags = db.Column(db.Integer)
    deaths = db.Column(db.Integer)
    wid = db.Column(db.Integer, primary_key=True)
    timeactive = db.Column(db.Integer)

    def __repr__(self):
        return '<GamePlayer %d from %d (%s [%s])>' % (
            self.wid, self.game_id, self.name, self.handle)

    def bombings(self):
        return [b.to_dict() for b in GameBombing.query.filter(
            and_(GameBombing.game == self.game_id,
                GameBombing.player == self.wid)).all()]

    def captures(self):
        return [b.to_dict() for b in GameCapture.query.filter(
            and_(GameCapture.game == self.game_id,
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

    game_id = db.Column('game',
                        db.Integer, db.ForeignKey('games.id'),
                        primary_key=True)
    game = db.relationship('Game',
                           backref=db.backref('server', lazy='dynamic'))
    handle = db.Column(db.Text)
    flags = db.Column(db.Text)
    desc = db.Column(db.Text)
    version = db.Column(db.Text)
    host = db.Column(db.Text)
    port = db.Column(db.Integer)

    def __repr__(self):
        return '<GameServer %s from %d)>' % (self.handle, self.game_id)

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "handle", "flags", "desc", "version", "host", "port"
        ])
