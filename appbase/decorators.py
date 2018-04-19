import datetime
try:
    import _pickle as pickle
except:
    import pickle
import redis
import sys
import traceback

from functools import wraps

from appbase.helpers import notify_dev, make_key_from_params
from settings import REDIS_HOST, REDIS_PORT, REDIS_DB

#TODO: Move below settings to settings/converge
NOTIFICATION_GAP = datetime.timedelta(0, (10*60))
CACHE_TTL = 3 * 7 * 24 * 60 * 60

# Not using decode_responses=True, 
# because pickle generates binary serialization format which doesn't have decode method
rconn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def failsafe(f):
    """This decorator can be used for making any function fail safe.
    Basically, at every call it would save the output against a key,
    uniquely created by function name and args, kw passed to the function.

    And in case of error it will return the previously saved output and will notify dev about error.
    """
    f.last_notified_at = datetime.datetime.now() - NOTIFICATION_GAP
    @wraps(f)
    def wrapper(*args, **kw):
        key = make_key_from_params(f.__name__, args, kw, strict=True)
        try:
            result = f(*args, **kw)
            rconn.set(key, pickle.dumps(result))
            rconn.expire(key, CACHE_TTL)
        except Exception as e:
            print(traceback.format_exc())
            now = datetime.datetime.now()
            if (now - f.last_notified_at) > NOTIFICATION_GAP:
                notify_dev(traceback.format_exc(), f.__name__, now)
                f.last_notified_at = now
            dump = rconn.get(key)
            result = pickle.loads(dump) if dump else None
        return result
    return wrapper
