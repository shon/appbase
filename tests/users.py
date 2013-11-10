from gevent.local import local

import appbase.users.apis as userapis
from appbase.publishers import satransaction
import appbase.sa as sa
import appbase.users.sessions as sessionslib


test_user_data = dict(fname='Peter', lname='Parker', email='pepa@example.com', password='Gwen')
test_user_id = 1


def setUp():
    sa.metadata.drop_all(sa.engine)
    sa.metadata.create_all(sa.engine)


def test_create():
    create = satransaction(userapis.create)
    assert create(**test_user_data) == 1


def test_authenticate():
    authenticate = satransaction(userapis.authenticate)
    assert authenticate(test_user_data['email'], test_user_data['password'])


def test_sessions():
    uid, k, v = 98765, 'foo', 'bar'
    d = sessionslib.get_or_create(uid)
    assert 'sid' in d
    d = sessionslib.get_or_create(uid)
    assert 'sid' in d
    sessionslib.add_to_session(uid, {k: v})
    d = sessionslib.get(uid)
    assert d[k] == v
    sessionslib.remove_from_session(uid, k)
    d = sessionslib.get(uid)
    assert k not in d
    sessionslib.destroy(uid)
    assert sessionslib.get(uid) == {}

def test_session_lookups():
    uids = xrange(10000, 10010)
    for uid in uids:
        sess = sessionslib.get_or_create(uid)
        sid = sess['sid']
        assert sessionslib.rev_lookup(sid) == uid
        sessionslib.destroy(uid)
        assert sessionslib.rev_lookup(sid) is None
