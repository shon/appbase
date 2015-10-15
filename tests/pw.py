import logging

from nose.tools import raises
from peewee import IntegerField, CharField

import appbase.bootstrap as bootstrap

from appbase.publishers import dbtransaction
import appbase.pw as pw

logger = logging.getLogger('peewee')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

class SomeThing(pw.BaseModel):
    name = CharField()


themodels = [SomeThing]


def create():
    return SomeThing.create(name='some name')


def create_err():
    create()
    raise Exception('Test Exception')


t_create = dbtransaction(create)
t_create_err = dbtransaction(create_err)


def setUpModule():
    for model in themodels:
        if model.table_exists():
            pw.db.drop_tables(themodels, cascade=True)
    pw.db.create_tables(themodels)


def tearDownModule():
    pw.db.drop_tables(themodels)


def test_transaction():
    for i in xrange(100):
        try:
            t_create_err()
        except Exception:
            pass
    thing = t_create()
    things = list(SomeThing.select())
    assert len(things) == 1
