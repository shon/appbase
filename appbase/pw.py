import datetime
from functools import update_wrapper

from peewee import PrimaryKeyField, DateTimeField, BooleanField, Model
from playhouse.pool import PooledPostgresqlExtDatabase, PostgresqlExtDatabase
from playhouse.shortcuts import model_to_dict

import settings

db = PooledPostgresqlExtDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    max_connections=settings.DB_MAXCONNECTIONS,
    register_hstore=False,
    stale_timeout=60*2) # 2 minutes


class BaseModel(Model):
    class Meta:
        database = db
        only_save_dirty = True

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
        print('connections in use: [%s]' % len(db._in_use))
        try:
            with db.atomic() as txn:
                result = f(*args, **kw)
                print('connections in use: [%s]' % len(db._in_use))
        finally:
            if not db.is_closed():
                db.close()
        return result

    update_wrapper(wrapper, f, ('__name__', 'cache',))
    return wrapper
