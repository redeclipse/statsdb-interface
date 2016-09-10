# -*- coding: utf-8 -*-
from statsdbinterface.database import db
from statsdbinterface.modelutils import direct_to_dict


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

    def to_dict(self):
        return direct_to_dict(self, [
                "id", "time",
                "map", "mode", "mutators",
                "timeplayed", "uniqueplayers",
                "usetotals"
            ],
            {
                "players": [p.to_dict() for p in self.players]
            })


class GamePlayer(db.Model):
    __tablename__ = 'game_players'

    game_id = db.Column('game',
        db.Integer, db.ForeignKey('games.id'), primary_key=True)
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

    def to_dict(self):
        return direct_to_dict(self, [
            "game_id", "name", "handle",
            "score", "timealive", "frags", "deaths", "wid", "timeactive"
            ])
