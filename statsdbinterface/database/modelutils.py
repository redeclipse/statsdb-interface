def direct_to_dict(base, attributes, update=None):
    """
    Return a dict from base's attributes.
    """

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


def list_to_id_dict(base, attribute):
    """
    Return a dict from an attribute in a list of dicts.
    """

    ret = {}

    for d in base:
        ret[d[attribute]] = d

    return ret
