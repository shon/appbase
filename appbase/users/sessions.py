import redis
import pickle
from base64 import b64encode, b64decode

import appbase.context as context
from appbase.helpers import gen_random_token as gen_sid
from appbase.errors import InvalidSessionError

import settings

rconn = redis.Redis(
    host=settings.SESSIONS_DB_HOST,
    port=settings.SESSIONS_DB_PORT,
    password=settings.SESSIONS_DB_PASSWORD,
    db=settings.SESSIONS_DB_NO
    )

session_key = lambda sid: 'session:' + sid
rev_lookup_key = 'uid:sid'


def create(uid='', groups=[], extras={}, ttl=(30 * 24 * 60 * 60)):
    """
    extras (dict): each key-value pair of extras get stored into hset
    """
    if uid:
        sid = rconn.hget(rev_lookup_key, uid)
        if sid:
            return sid.decode()
    sid = gen_sid()
    rconn.hset(session_key(sid), 'uid', pickle.dumps(uid))
    rconn.hset(session_key(sid), 'groups', pickle.dumps(groups))
    for key, value in extras.items():
        rconn.hset(session_key(sid), key, pickle.dumps(value))
    rconn.hset(rev_lookup_key, uid, sid)
    return sid


def exists(sid):
    return rconn.exists(session_key(sid))


def get(sid, keys=[]):
    s_values = rconn.hgetall(session_key(sid))
    if not s_values:
        raise InvalidSessionError()
    session = {k.decode(): pickle.loads(v) for k, v in s_values.items()}
    if keys:
        session = {k: session.get(k, None) for k in keys}
    return session


def get_attribute(sid, attribute):
    value = rconn.hget(session_key(sid), attribute)
    return pickle.loads(value) if value else None


def get_for(uid):
    sid = rconn.hget(rev_lookup_key, uid)
    return get(sid.decode()) if sid else None


def uid2sid(uid):
    sid = rconn.hget(rev_lookup_key, uid)
    return sid.decode() if sid else None


def sid2uidgroups(sid):
    """
    => uid (int), groups (list)
    """
    session = get(sid, ['uid', 'groups'])
    return session['uid'], session['groups']


def update(sid, keyvalues):
    sk = session_key(sid)
    keyvalues = {k: pickle.dumps(v) for k, v in list(keyvalues.items())}
    rconn.hmset(sk, keyvalues)
    return True


def update_for(uid, keyvalues):
    sid = uid2sid(uid)
    return update(sid, keyvalues) if sid else None


def update_attribute(sid, attribute, value):
    key = session_key(sid)
    rconn.hset(key, attribute, pickle.dumps(value))
    return True


def remove_from_session(sid, keys):
    sk = session_key(sid)
    rconn.hdel(sk, keys)
    return True


def destroy(sid):
    uid = sid2uidgroups(sid)[0]
    sk = session_key(sid)
    rconn.delete(sk)
    rconn.hdel(rev_lookup_key, uid)
    return True


def destroy_all():
    keys = rconn.keys(session_key('*'))
    rconn.delete(keys)
    keys = rconn.keys(rev_lookup_key + '*')
    rconn.delete(keys)


# Simple debugging helper
def whoami():
    sid = hasattr(context.current, 'sid') and context.current.sid
    uid, groups = None, None
    if sid:
        uid, groups = sid2uidgroups(sid)
    return {'sid': sid, 'uid': uid, 'groups': groups}
