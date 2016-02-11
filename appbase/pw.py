import sys
import datetime
if sys.version[0] == '2':
    from functools32 import wraps
else:
    from functools import wraps
from enum import Enum

from peewee import DateTimeField, Model
from playhouse.pool import PooledPostgresqlExtDatabase
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

    def to_dict(self, only=None, recurse=False):
        return model_to_dict(self, only=only, recurse=recurse)


class CommonModel(BaseModel):
    created = DateTimeField(default=datetime.datetime.utcnow)


def dbtransaction(f):
    """
    wrapper that make db transactions automic
    note db connections are used only when it is needed (hence there is no usual connection open/close)
    """
    @wraps(f)
    def wrapper(*args, **kw):
        try:
            with db.transaction():
                result = f(*args, **kw)
        finally:
            if not db.is_closed():
                db.close()
        return result
    return wrapper


def enumify(TheModel, name_field='name', val_field='id'):
    """
    Converts a model rowa into an enum
    Can be effective cache for mostly unchanging data.
    Limitation: No auto updates. If you update the model and you are using process manager like gunicorn you
    would need to restart to rnsure enums are updated

    eg.
    >>> class Week(BaseModel):
            day = CharField()
            num = IntField()

    >>> weekenum = enumify(Week, 'day', 'num')
    >>> print(weekenum.monday.num)
    """
    fields = getattr(TheModel, name_field), getattr(TheModel, val_field)
    data = list((name.replace(' ', '_').lower(), v) for (name, v) in TheModel.select(*fields).tuples())
    return Enum(TheModel.__name__, data)
