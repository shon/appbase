from nose.tools import raises

import appbase.bootstrap as bootstrap
import appbase.redisutils as redisutils

import appbase.users.apis as userapis
import appbase.users.stats as stats
from appbase.publishers import satransaction
import appbase.sa as sa
import appbase.users.sessions as sessionslib
from  appbase.users.errors import InvalidEmailError, EmailExistsError, PasswordTooSmallError


test_user_data = dict(fname='Peter', lname='Parker', password='Gwen7', email='pepa@localhost.localdomain')
test_user_data_grp = dict(fname='Peter', lname='Parker', password='Gwen7', email='pepa2@localhost.localdomain', groups=['admin', 'member'])
test_user_data_iv = dict(fname='Peter', lname='Parker', password='Gwen7', email='pepa @ localhost.localdomain')
test_user_data_sp = dict(fname='Peter', lname='Parker', password='Gwen', email='pepa @ localhost.localdomain')
test_user_id = 1
signup_user_data = dict(fname='Clark', lname='Kent', email='ckent@localhost.localdomain', password='secret')


create = satransaction(userapis.create)
count = satransaction(stats.count)
info = satransaction(userapis.info)
signup = satransaction(userapis.signup)
complete_signup = satransaction(userapis.complete_signup)
authenticate = satransaction(userapis.authenticate)

rconn = redisutils.rconn


def setUpModule():
    sa.metadata.create_all(sa.engine)


def tearDownModule():
    sa.metadata.drop_all(sa.engine)
    rconn.flushall()


def test_create_invalid_email():
    try:
        create(**test_user_data_iv)
        assert False, 'must raise InvalidEmailError'
    except InvalidEmailError as err:
        email = test_user_data_iv['email']
        assert email == err.data['email']


def test_create_small_password():
    try:
        create(**test_user_data_sp)
        assert False, 'must raise PasswordTooSmallError'
    except PasswordTooSmallError as err:
        assert 'characters' in err.msg


def test_create():
    last_count = count()
    assert isinstance(create(**test_user_data), int)
    d = info(test_user_data['email'])
    assert d['active'] is True
    assert d['fname'] == test_user_data['fname']
    assert (count() - last_count) == 1


def test_create_w_groups():
    last_count = count()
    assert isinstance(create(**test_user_data_grp), int)
    d = info(test_user_data_grp['email'])
    assert d['groups'] == test_user_data_grp['groups']
    assert d['active'] is True
    assert d['fname'] == test_user_data_grp['fname']
    assert (count() - last_count) == 1


def test_info():
    d = info(test_user_data['email'])
    assert d['fname'] == test_user_data['fname']
    d = info(test_user_data['email'].upper())
    assert d['fname'] == test_user_data['fname']


def test_create_duplicate():
    try:
        create(**test_user_data)
        assert False, 'must raise EmailExistsError'
    except EmailExistsError as err:
        email = test_user_data['email']
        assert email == err.data['email']


def test_signup():
    signup(**signup_user_data)
    token = userapis.signupemail2token(signup_user_data['email'])
    sid = complete_signup(token)
    uid, groups = sessionslib.sid2uidgroups(sid)
    d = info(signup_user_data['email'])
    assert d['id'] == uid
    assert d['groups'] == groups
    assert d['active'] is True
    assert d['fname'] == signup_user_data['fname']


def test_authenticate():
    assert authenticate(test_user_data['email'], test_user_data['password'])


def test_authenticate_invalid():
    assert authenticate(test_user_data['email'], 'hopefully-incorrect') is None
    invalid_email = 'invalid @ email '
    try:
        authenticate(invalid_email, 'meaningless-password')
        assert False, 'must raise InvalidEmailError'
    except InvalidEmailError as err:
        assert invalid_email == err.data['email']


def test_sessions():
    uid, groups, k, v = 98765, ['admin', 'member'], 'foo', 'bar'
    sid = sessionslib.create(uid, groups)
    assert len(sid) > 43
    sid_new = sessionslib.create(uid, groups)
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
    groups = ['grp1', 'grp2']
    for uid in uids:
        sid = sessionslib.create(uid, groups)
        assert sessionslib.sid2uidgroups(sid) == uid, groups
        sessionslib.destroy(sid)
        assert sessionslib.get(sid) == {}
