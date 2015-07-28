import datetime

from peewee import PrimaryKeyField, DateTimeField, BooleanField, Model
from playhouse.pool import PooledPostgresqlExtDatabase, PostgresqlExtDatabase
from playhouse.shortcuts import model_to_dict

import settings

db = PooledPostgresqlExtDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    max_connections=32,
    register_hstore=False,
    stale_timeout=60*2) # 2 minutes


class BaseModel(Model):
    class Meta:
        database = db

    def to_dict(self, only=None):
        return model_to_dict(self, only=only)


class CommonModel(BaseModel):
    id = PrimaryKeyField()
    created = DateTimeField(default=datetime.datetime.now)
    active = BooleanField(default=True)


def tr_start():
    #db.connect()
    # explicitly connecting for each request is possibly not required and
    # needless to say it is slower.  peewee would connect anyway when model is
    # used.
    pass


def tr_complete():
    if not db.is_closed():
        db.close()
        print('complete: is_closed: ', db.is_closed())


def tr_abort():
    db.rollback()
    if not db.is_closed():
        db.close()
