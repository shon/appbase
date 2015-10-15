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
    def wrapper(*args, **kw):
        handlers_failed = False
        db.connect()
        with db.atomic() as txn:
            try:
                result = f(*args, **kw)
                return result
            except Exception as err:
                handlers_failed = True
        if not db.is_closed():
            db.close()
        if handlers_failed:
            raise
    return wrapper
