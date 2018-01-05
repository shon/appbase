# -*- coding: utf-8 -*-
import appbase.users.sessions as sessions


def test_create_session():

    sid = sessions.create()
    assert isinstance(sid, str) and len(sid) == 47


def test_get_session():

    sid = sessions.create()
    data = sessions.get(sid)
    assert data == {'sid': sid}


def test_get_attribute():

    sid = sessions.create()
    data = sessions.get(sid)
    data['prefs'] = {'last_seen': '10/05/2016'}
    assert sessions.update(sid, data)

    data = sessions.get(sid)
    assert data['prefs']['last_seen'] == '10/05/2016'

    value = sessions.get_attribute(sid, 'prefs')
    assert value['last_seen'] == '10/05/2016'

    value = sessions.get_attribute(sid, 'ar')
    assert value is None


def test_update_session():

    sid = sessions.create()
    data = sessions.get(sid)
    data['prefs'] = {'last_seen': '10/05/2016'}
    assert sessions.update(sid, data)

    data = sessions.get(sid)
    assert data['prefs']['last_seen'] == '10/05/2016'

    data['prefs'] = {'last_seen': '11/05/2016'}
    assert sessions.update(sid, data)

    data = sessions.get(sid)
    assert data['prefs']['last_seen'] == '11/05/2016'


def test_update_attribute():

    sid = sessions.create()
    assert sessions.update_attribute(sid, 'prefs', {'last_seen': '10/05/2016'})

    value = sessions.get_attribute(sid, 'prefs')
    assert value['last_seen'] == '10/05/2016'

    assert sessions.update_attribute(sid, 'prefs', {'last_seen': '11/05/2016'})

    value = sessions.get_attribute(sid, 'prefs')
    assert value['last_seen'] == '11/05/2016'


def test_delete_session():

    sid = sessions.create()
    data = sessions.get(sid)
    data['prefs'] = {'last_seen': '10/05/2016'}
    assert sessions.update(sid, data)

    data = sessions.get(sid)
    assert data['prefs']['last_seen'] == '10/05/2016'

    assert sessions.destroy(sid)

    data = sessions.get(sid)
    assert data == {}
