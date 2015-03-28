import datetime

from peewee import PrimaryKeyField, DateTimeField, BooleanField, Model
from playhouse.pool import PooledPostgresqlExtDatabase
from playhouse.shortcuts import model_to_dict

import settings

db = PooledPostgresqlExtDatabase(
    database=settings.DB_NAME,
    host=settings.DB_HOST,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    max_connections=32,
    stale_timeout=300)  # 5 minutes.


class BaseModel(Model):
    class Meta:
        database = db

    def to_dict(self):
        return model_to_dict(self)



class CommonModel(BaseModel):
    id = PrimaryKeyField()
    created = DateTimeField(default=datetime.datetime.now)
    active = BooleanField(default=True)


def tr_start():
    db.connect()


def tr_complete():
    if not db.is_closed():
        db.close()


def tr_abort():
    db.rollback()
