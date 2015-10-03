from nose.tools import raises
from peewee import CharField

import appbase.bootstrap as bootstrap

from appbase.publishers import dbtransaction
import appbase.pw as pw

test_data = dict(name='some name')


class SomeThing(pw.BaseModel):
    name = CharField(null=False, unique=True)


themodels = [SomeThing]


def create():
    return SomeThing.create(name='some name')


def create_err():
    create()
    create()
    raise Exception('Test Exception')


create = dbtransaction(create)
create_err = dbtransaction(create_err)


def setUpModule():
    for model in themodels:
        if model.table_exists():
            pw.db.drop_tables(themodels, cascade=True)
    pw.db.create_tables(themodels)


def tearDownModule():
    pw.db.drop_tables(themodels)


def test_transaction():
    try:
        create_err()
    except Exception:
        pass
    thing = create()
    things = list(SomeThing.select())
    assert len(things) == 1
