from nose.tools import raises

import appbase.bootstrap as bootstrap

import appbase.users.apis as userapis
from appbase.publishers import satransaction
import appbase.sa as sa
import appbase.users.sessions as sessionslib
from  appbase.users.errors import InvalidEmailError, EmailExistsError


test_user_data = dict(fname='Peter', lname='Parker', password='Gwen', email='pepa@localhost.localdomain')
test_user_data_iv = dict(fname='Peter', lname='Parker', password='Gwen', email='pepa @ localhost.localdomain')
test_user_id = 1
signup_user_data = dict(fname='Clark', lname='Kent', email='ckent@localhost.localdomain', password='secret')


def setUp():
    sa.metadata.drop_all(sa.engine)
    sa.metadata.create_all(sa.engine)


def test_create_invalid_email():
    create = satransaction(userapis.create)
    try:
        create(**test_user_data_iv)
        assert False, 'must raise InvalidEmailError'
    except InvalidEmailError as err:
        email = test_user_data_iv['email']
        assert email in err.msg
        assert email == err.data['email']


def test_create():
    create = satransaction(userapis.create)
    count = satransaction(userapis.count)
    info = satransaction(userapis.info)
    assert create(**test_user_data) == 1
    d = info(test_user_data['email'])
    assert d['active'] is True
    assert d['fname'] == test_user_data['fname']
    assert count() == 1


def test_info():
    info = satransaction(userapis.info)
    d = info(test_user_data['email'])
    assert d['fname'] == test_user_data['fname']
    d = info(test_user_data['email'].upper())
    assert d['fname'] == test_user_data['fname']


def test_create_duplicate():
    create = satransaction(userapis.create)
    try:
        create(**test_user_data)
        assert False, 'must raise EmailExistsError'
    except EmailExistsError as err:
        email = test_user_data['email']
        assert email in err.msg
        assert email == err.data['email']


def test_signup():
    signup = satransaction(userapis.signup)
    complete_signup = satransaction(userapis.complete_signup)
    info = satransaction(userapis.info)
    signup(**signup_user_data)
    token = userapis.signupemail2token(signup_user_data['email'])
    assert isinstance(complete_signup(token), int)
    d = info(signup_user_data['email'])
    assert d['active'] is True
    assert d['fname'] == signup_user_data['fname']


def test_authenticate():
    authenticate = satransaction(userapis.authenticate)
    assert authenticate(test_user_data['email'], test_user_data['password'])


def test_sessions():
    uid, k, v = 98765, 'foo', 'bar'
    sid = sessionslib.create(uid)
    assert len(sid) > 43
    sid_new = sessionslib.create(uid)
    assert sid == sid_new
    sessionslib.add_to_session(sid, {k: v})
    d = sessionslib.get(sid)
    assert d[k] == v
    sessionslib.remove_from_session(sid, k)
    d = sessionslib.get(sid)
    assert k not in d
    sessionslib.destroy(sid)
    assert sessionslib.get(sid) == {}


def test_session_lookups():
    uids = xrange(10000, 10010)
    for uid in uids:
        sid = sessionslib.create(uid)
        assert sessionslib.sid2uid(sid) == uid
        sessionslib.destroy(sid)
        assert sessionslib.get(sid) == {}
