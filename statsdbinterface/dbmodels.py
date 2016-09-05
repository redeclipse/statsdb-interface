# -*- coding: utf-8 -*-
from statsdbinterface.database import db


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
        return '<Game %r>' % (self.id)

    def to_dict(self):
        return {
            "id": self.id,
            "time": self.time,
            "map": self.map,
            "mode": self.mode,
            "mutators": self.mutators,
            "timeplayed": self.timeplayed,
            "uniqueplayers": self.uniqueplayers,
            "usetotals": self.usetotals,
        }
