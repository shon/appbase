import sys
sys.path.append('.')

import appbase.bootstrap as bootstrap
bootstrap.use_gevent()
bootstrap.green_pg()
#bootstrap.check_settings('test')

import gevent
import json
import unittest

from flask import Flask

import appbase.publishers
import appbase.sa as sa
import appbase.users.apis as userapis
import appbase.users.sessions as sessionslib
import appbase.redisutils as redisutils


def add(a, b):
    return a + b
add.roles_required = ['admin']


def setup_module():
    teardown_module()
    sa.metadata.create_all(sa.engine)


def teardown_module():
    sa.metadata.drop_all(sa.engine)
    redisutils.rconn.flushall()


class RESTPublisherTestCase(unittest.TestCase):
    """
    Tests for the RESTPublisher Class.
    These tests use the externally defined functions
    for the resource to to published, i.e. users.
    """
    def setUp(self):
        self.app = Flask(__name__)
        # Creating a RESTPublisher
        rest_publisher = appbase.publishers.RESTPublisher(self.app)
        http_publisher = appbase.publishers.HTTPPublisher(self.app)
        handlers = (userapis.list_, userapis.create, None, userapis.info, userapis.edit, userapis.remove)
        rest_publisher.map_resource('users/', handlers, resource_id=('int', 'id'))
        self.client = self.app.test_client()
        self.test_user_data = dict(password='Gwen7', email='pepa2@localhost.localdomain', groups=['admin', 'member'])
        http_publisher.add_mapping('/api/add', add, ['POST'])

    def test_add_user_no_session(self):
        resp = self.client.post('/api/users/', data=json.dumps(self.test_user_data))
        assert resp.status_code == 200
        uid = json.loads(resp.data)['result']
        resp = self.client.post('/api/add', data=json.dumps({'a': 1, 'b': 2}))
        self.assertEquals(resp.status_code, 403)
        sid = sessionslib.create(uid, self.test_user_data['groups'])
        self.client.set_cookie('localhost.localdomain', 'session_id', sid)
        resp = self.client.post('/api/add', data=json.dumps({'a': 1, 'b': 2}))
        assert resp.status_code == 200
        assert json.loads(resp.data)['result'] == 3
