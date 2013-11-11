import appbase.redisutils as redisutils
from appbase.helpers import gen_random_token as gen_sid

rconn = redisutils.rconn
session_key = lambda uid: 'sid:' + str(uid)
rev_lookup_key = 'session:uid'


def create(uid, ttl=(30 * 24 * 60 * 60)):
    sid = gen_sid()
    rconn.hset(session_key(uid), 'sid', sid)
    rconn.hset(rev_lookup_key, sid, uid)
    return {'sid': sid}


def get(uid):
    return rconn.hgetall(session_key(uid))


def sid2uid(sid):
    uid = rconn.hget(rev_lookup_key, sid)
    if uid:
        return int(uid)


def get_or_create(uid):
    return get(uid) or create(uid)


def add_to_session(uid, keyvalues):
    sk = session_key(uid)
    rconn.hmset(sk, keyvalues)
    return True


def remove_from_session(uid, keys):
    sk = session_key(uid)
    rconn.hdel(sk, keys)
    return True


def destroy(uid):
    sk = session_key(uid)
    sess = get(uid)
    sid = sess['sid']
    rconn.delete(sk)
    rconn.hdel(rev_lookup_key, sid)
    return True
