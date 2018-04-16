import datetime
import json
import sys
import traceback

from functools import wraps

from appbase.helpers import notify_dev, make_key_from_params
import appbase.redisutils as redisutils

#TODO: Move below settings to settings/converge
NOTIFICATION_GAP = datetime.timedelta(0, (10*60))
CACHE_TTL = 3 * 7 * 24 * 60 * 60

rconn = redisutils.rconn


def failsafe(f):
    """This decorator can be used for making any function fail safe.
    Basically, at every call it would save the output against a key,
    uniquely created by function name and args, kw passed to the function.

    And in case of error it will return the previously saved output and will notify tech about error.
    """
    f.last_notified_at = datetime.datetime.now() - NOTIFICATION_GAP
    @wraps(f)
    def wrapper(*args, **kw):
        key = make_key_from_params(f.__name__, args, kw, strict=True)
        try:
            result = f(*args, **kw)
            rconn.set(key, json.dumps(result, default=str))
            rconn.expire(key, CACHE_TTL)
        except Exception as e:
            print(traceback.format_exc())
            now = datetime.datetime.now()
            if (now - f.last_notified_at) > NOTIFICATION_GAP:
                notify_dev(traceback.format_exc(), f.__name__, now)
                f.last_notified_at = now
            result = json.loads(rconn.get(key) or 'null')
        return result
    return wrapper
