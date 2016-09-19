# -*- coding: utf-8 -*-

from collections import OrderedDict
from ..dbmodels import Game

DEFAULT_VERSION = "1.5.6"

registry = []
game_cache = {}
version_cache = {}


def version_str_to_tuple(s):
    return tuple([int(n) for n in s.split('.')])


def get_version_class(version):
    if version in version_cache:
        return version_cache[version]

    vtuple = version_str_to_tuple(version)
    for vclass in registry:
        if vtuple >= vclass.start and vtuple <= vclass.end:
            version_cache[version] = vclass
            return version_cache[version]

    # If we can't find the version, try defaulting.
    if version != DEFAULT_VERSION:
        version_cache[version] = get_version_class(DEFAULT_VERSION)
        return version_cache[version]

    # No class supports DEFAULT_VERSION, something is wrong.
    assert False, ("No version class for DEFAULT_VERSION (%s) found." % (
        DEFAULT_VERSION))


def get_game_version(game_id):
    if game_id not in game_cache:
        game_cache[game_id] = Game.query.filter(
            Game.id == game_id).first().server[0].version
    return get_version_class(game_cache[game_id])


def reversion(c):
    registry.append(c())
    return c


class RE:

    def __init__(self):
        #Core mode names
        self.cmodestr = {}
        for k, v in list(self.modes.items()):
            self.cmodestr[v] = k

        def tomuts(l, a=0):
            ret = OrderedDict()
            for i, mut in enumerate(l):
                ret[mut] = 1 << (i + a)
            return ret

        #Create Mutator Lists
        gspnum = self.basemuts.index("gsp")
        self.basemuts = tomuts(self.basemuts)
        del self.basemuts["gsp"]
        self.mutators.update(self.basemuts)
        for mode, modemuts in list(self.gspmuts.items()):
            modemuts = tomuts(modemuts, gspnum)
            self.gspmuts[mode] = modemuts
            self.mutators.update(modemuts)

        self.start = version_str_to_tuple(self.start)
        self.end = version_str_to_tuple(self.end)

    def mutslist(self, mode, mutators):
        muts = []

        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        for m in self.basemuts:
            if (mutators & self.basemuts[m]):
                muts.append(m)

        if mode in self.gspmuts:
            for m in self.gspmuts[mode]:
                if (mutators & self.gspmuts[mode][m]):
                    muts.append(m)

        return muts


@reversion
class RE_1_5_dev(RE):
    # Limits
    start = "1.5.4"
    end = "1.5.6"

    # Weapon Lists
    loadoutweaponlist = ["sword", "shotgun",
        "smg", "flamer", "plasma", "zapper", "rifle"]
    weaponlist = [
        "claw", "pistol"
        ] + loadoutweaponlist + [
        "grenade", "mine", "rocket", "melee"]
    notwielded = ["melee"]

    #Mode Lists
    modes = {
        "dm": 2,
        "ctf": 3,
        "dac": 4,
        "bb": 5,
        "race": 6,
        }

    #Mutators
    mutators = {}
    basemuts = ["multi", "ffa", "coop", "insta", "medieval", "kaboom",
        "duel", "survivor", "classic", "onslaught", "freestyle", "vampire",
        "resize", "hard", "basic", "gsp"]
    gspmuts = {
        modes["ctf"]: ["quick", "defend", "protect"],
        modes["dac"]: ["quick", "king"],
        modes["bb"]: ["hold", "basket", "attack"],
        modes["race"]: ["timed", "endurance", "gauntlet"],
        modes["dm"]: ["gladiator", "oldschool"],
        }

    #Fancy Mode Names
    modestr = ["Demo", "Editing", "Deathmatch",
        "CTF", "DAC", "Bomber Ball", "Race"]
