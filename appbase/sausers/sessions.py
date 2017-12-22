import appbase.redisutils as redisutils
from appbase.helpers import gen_random_token as gen_sid
from base64 import b64encode, b64decode

rconn = redisutils.rconn
session_key = lambda sid: 'session:' + sid
rev_lookup_key = 'uid:sid'


def create(uid, groups, ttl=(30 * 24 * 60 * 60)):
    sid = rconn.hget(rev_lookup_key, uid)
    if sid:
        return sid
    uidgroups = str(uid) + ':' + (':'.join(groups) if groups else '')
    sid = gen_sid() + b64encode(uidgroups)
    rconn.hset(session_key(sid), 'sid', sid)
    rconn.hset(rev_lookup_key, uid, sid)
    return sid


def get(sid):
    return rconn.hgetall(session_key(sid))


def get_for(uid):
    sid = rconn.hget(rev_lookup_key, uid)
    return get(sid)


def sid2uidgroups(sid):
    """
    => uid (int), groups (list)
    """
    uidgroups_list = b64decode(sid[43:]).split(b':')
    uid = int(uidgroups_list[0])
    groups = uidgroups_list[1:]
    return uid, groups


def add_to_session(sid, keyvalues):
    sk = session_key(sid)
    rconn.hmset(sk, keyvalues)
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
