from flask import abort
from flask_sqlalchemy import Pagination


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


def to_pagination(page, per_page, page_function, count_function):
    if page < 1 or per_page < 1:
        abort(404)
    items = page_function(page - 1, per_page)
    if not items and page != 1:
        abort(404)
    if page == 1 and len(items) < per_page:
        total = len(items)
    else:
        total = count_function()
    return Pagination(None, page, per_page, total, items)
