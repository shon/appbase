import appbase.redisutils as redisutils
from appbase.helpers import gen_random_token as gen_sid

rconn = redisutils.rconn
session_key = lambda sid: 'session:' + sid
rev_lookup_key = 'uid:sid'


def create(uid, ttl=(30 * 24 * 60 * 60)):
    sid = rconn.hget(rev_lookup_key, uid)
    if sid:
        return sid
    sid = gen_sid() + hex(uid)[2:]
    rconn.hset(session_key(sid), 'sid', sid)
    rconn.hset(rev_lookup_key, uid, sid)
    return sid


def get(sid):
    return rconn.hgetall(session_key(sid))


def get_for(uid):
    sid = rconn.hget(rev_lookup_key, uid)
    return get(sid)


def sid2uid(sid):
    return int(sid[43:], 16)


def add_to_session(sid, keyvalues):
    sk = session_key(sid)
    rconn.hmset(sk, keyvalues)
    return True


def remove_from_session(sid, keys):
    sk = session_key(sid)
    rconn.hdel(sk, keys)
    return True


def destroy(sid):
    uid = sid2uid(sid)
    sk = session_key(sid)
    rconn.delete(sk)
    rconn.hdel(rev_lookup_key, sid)
    return True
