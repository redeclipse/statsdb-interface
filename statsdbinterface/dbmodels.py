# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Text
from statsdbinterface.database import Base


class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    time = Column(Integer)
    map = Column(Text)
    mode = Column(Integer)
    mutators = Column(Integer)
    timeplayed = Column(Integer)
    uniqueplayers = Column(Integer)
    usetotals = Column(Integer)

    def __repr__(self):
        return '<Game %r>' % (self.id)
