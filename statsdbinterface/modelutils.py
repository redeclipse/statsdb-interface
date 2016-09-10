# -*- coding: utf-8 -*-


# Return a dict from base's attributes.
def direct_to_dict(base, attributes, update=None):
    ret = {}
    for attr in attributes:
        if type(attr) is tuple:
            # Different name in the output.
            ret[attr[1]] = getattr(base, attr[0])
        else:
            # Same name in the output.
            ret[attr] = getattr(base, attr)
    if update:
        ret.update(update)
    return ret


# Return a dict from an attribute in a list of dicts.
def list_to_id_dict(base, attribute):
    ret = {}
    for d in base:
        ret[d[attribute]] = d
    return ret
