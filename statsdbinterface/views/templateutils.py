# -*- coding: utf-8 -*-
import time


def timestr(epoch_time, output_format="%F %T %Z"):
    """
    Return epoch_time as a GMT time string.
    """
    return time.strftime(output_format, time.gmtime(epoch_time))


def timeago(epoch_time, short=False):
    """
    Return time elapsed since epoch_time
    """
    difference = time.time() - epoch_time

    # <sconds>, <long name>, <short name>, <maximum before rounding>
    levels = [
        (60 * 60 * 24 * 365.25, "year", "y", 0),
        (60 * 60 * 24 * 7, "week", "w", 52 * 2),
        (60 * 60 * 24, "day", "d", 7 * 2),
        (60 * 60, "hour", "h", 24 * 2),
        (60, "minute", "m", 60 * 2),
        (1, "second", "s", 60),
    ]

    ret = ""
    remaining = difference

    for seconds, long_name, short_name, maximum in levels:
        of_this = remaining // seconds
        remaining = remaining % seconds
        if maximum and difference / seconds > maximum:
            break
        if of_this > 0:
            rounded = round(of_this)
            formatted_long_name = (
                long_name if rounded == 1 else (long_name + 's'))
            ret += '%d%s ' % (
                rounded, short_name if short else (" " + formatted_long_name))

    return (ret or ('0' + (levels[-1][3] if short else levels[-1][2]))).strip()
