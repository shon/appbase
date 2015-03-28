import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField
from playhouse.postgres_ext import ArrayField

from appbase.pw import BaseModel, CommonModel


class User(CommonModel):
    email = CharField(null=False, unique=True, index=True)
    password = CharField()
    groups = ArrayField(CharField, default=[])


class GroupUser(BaseModel):
    created = DateTimeField(default=datetime.datetime.now)
    ctx = IntegerField(default=0)
    user_id = ForeignKeyField(User, null=False, on_delete='CASCADE')
    group = CharField(null=False)
