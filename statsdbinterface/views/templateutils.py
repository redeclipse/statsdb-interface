# -*- coding: utf-8 -*-
import time


def time_str(epoch_time, output_format="%F %T %Z"):
    """
    Return epoch_time as a GMT time string.
    """
    return time.strftime(output_format, time.gmtime(epoch_time))


def duration_str(difference, short=False, exact=False, decimal=False):
    """
    Return difference as a human-readable string.
    """
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
        use_decimal = (decimal and seconds == 1)
        if use_decimal:
            of_this = remaining / seconds
            remaining = 0
        else:
            of_this = remaining // seconds
            remaining = remaining % seconds
        if not exact and maximum and difference / seconds > maximum:
            break
        if of_this > 0:
            if use_decimal:
                rounded = round(of_this, 3)
            else:
                rounded = round(of_this)
            formatted_long_name = (
                long_name if rounded == 1 else (long_name + 's'))
            if use_decimal:
                ret += '%.3f%s ' % (
                    rounded, short_name if short else
                    (" " + formatted_long_name))
            else:
                ret += '%d%s ' % (
                    rounded, short_name if short else
                    (" " + formatted_long_name))

    return (ret or ('0' + (levels[-1][2] if short else levels[-1][1]))).strip()


def time_ago(epoch_time, short=False):
    """
    Return time elapsed since epoch_time
    """
    difference = time.time() - epoch_time

    return duration_str(difference, short=short)


def sdiv(n):
    """
    Safe division clamp, ensure n is not less than 1.
    """
    return max(1, n)


def register(bp):
    bp.app_template_filter()(sdiv)
    bp.app_template_filter()(time_ago)
    bp.app_template_filter()(time_str)
    bp.app_template_filter()(duration_str)
