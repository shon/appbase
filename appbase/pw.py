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
        return model_to_dict(self, only=only, recurse=False)


class CommonModel(BaseModel):
    created = DateTimeField(default=datetime.datetime.now)


def dbtransaction(f):
    """
    wrapper that make db transactions automic
    note db connections are used only when it is needed (hence there is no usual connection open/close)
    """
    def wrapper(*args, **kw):
        #print('connections in use: [%s]' % db._in_use)
        with db.atomic() as txn:
            result = f(*args, **kw)
            #print('connections in use: [%s]' % db._in_use)
        if not db.is_closed():
            db.close()
        return result
    return wrapper
