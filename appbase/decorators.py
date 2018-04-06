import sys
import datetime
import json
import traceback

if sys.version[0] == '2':
    from functools32 import wraps
else:
    from functools import wraps

from appbase.helpers import notify_tech, make_key_of_params
import appbase.redisutils as redisutils

NEXT_NOTIFICATION_GAP = datetime.timedelta(0, (10*60))
CACHE_TTL = 3 * 7 * 24 * 60 * 60
rconn = redisutils.rconn


def fail_safe(f):
    """This decorator can be used for making any function fail safe.
    Basically, at every call it would save the output against a key,
    uniquely created by function name and args, kwds passed to the function.

    And in case of error it will return the previously saved output and will notify tech about error.
    """
    f.last_notified_at = datetime.datetime.now() - NEXT_NOTIFICATION_GAP
    @wraps(f)
    def wrapper(*args, **kwds):
        key = make_key_of_params(args, kwds, f.__name__, seperator='fail_safe', strict=False)
        try:
            result = f(*args, **kwds)
            rconn.set(key, json.dumps(result, default=str))
            rconn.expire(key, CACHE_TTL)
        except Exception as e:
            now = datetime.datetime.now()
            if (now - f.last_notified_at) > NEXT_NOTIFICATION_GAP:
                notify_tech(traceback.format_exc(), f.__name__, now)
                f.last_notified_at = now
            result = json.loads(rconn.get(key) or 'null')
        return result
    return wrapper
