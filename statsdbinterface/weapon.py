from .utils import result_to_dict

loadout = ("sword", "shotgun", "smg", "flamer", "plasma", "zapper",
           "rifle")

all = ("claw", "pistol") + loadout + ("grenade", "mine", "rocket", "melee")

standard = ("claw", "pistol") + loadout + ("melee",)

not_wielded = ("melee",)


defaults = {'timeloadout': 0,
            'timewielded': 0,
            'damage1': 0,
            'damage2': 0,
            'flakhits1': 0,
            'flakhits2': 0,
            'flakshots1': 0,
            'flakshots2': 0,
            'frags1': 0,
            'frags2': 0,
            'hits1': 0,
            'hits2': 0,
            'shots1': 0,
            'shots2': 0,
            'name': None}
default_keys = tuple(defaults.keys())


def default(name, keys=default_keys):
    weapon = {k: defaults[k] for k in keys}
    weapon['name'] = name
    return weapon


def ordered(weapons, order=all):
    keys = weapons[0].keys() if len(weapons) > 0 else default_keys
    weapons = {w.name: w for w in weapons}
    ordered = []
    for wname in order:
        if wname in weapons:
            ordered.append(result_to_dict(weapons[wname]))
        else:
            ordered.append(default(wname, keys))
    return ordered
