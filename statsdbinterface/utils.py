import time
from collections import namedtuple
from flask import current_app, request
from werkzeug.exceptions import NotFound


def page_number():
    return request.args.get('page', default=1, type=int)


def page_size():
    return current_app.config['DISPLAY_RESULTS_PER_PAGE']


def page(query):
    p, ps = page_number(), page_size()
    return query.offset((p - 1) * ps).limit(ps)


Pager = namedtuple('Pager', 'items has_prev has_next prev_num next_num')
""" Replaces `flask_sqlalchemy.Pagination` to make sure it's `next`
and `prev` methods (which can execute count query) aren't used.
"""


def pager(query, count_fn=None):
    """ Supports custom count function, unlike
    `flask_sqlalchemy.BaseQuery.pagination`.
    """
    p, ps = page_number(), page_size()
    if p < 1:
        raise NotFound
    items = page(query).all()
    if not items:
        raise NotFound
    if len(items) < ps:
        has_next = False
    else:
        if count_fn is None:
            count_fn = query.count
        has_next = p * ps < count_fn()
    return Pager(items,
                 has_prev=p > 1,
                 has_next=has_next,
                 prev_num=p - 1,
                 next_num=p + 1)


def recent(query):
    recent_count = current_app.config['DISPLAY_RESULTS_RECENT']
    return query.offset(0).limit(recent_count)


def result_to_dict(result):
    return {k: getattr(result, k) for k in result.keys()}


def raise404():
    raise NotFound


class classproperty(object):

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        return self.func(owner)


def days_ago(days):
    return time.time() - (days * 60 * 60 * 24)
