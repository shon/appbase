import datetime

from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, BooleanField
from playhouse.postgres_ext import ArrayField, BinaryJSONField

from appbase.pw import BaseModel, CommonModel


class User(CommonModel):
    class Meta:
        db_table = 'users'
    name = CharField(null=True)
    email = CharField(null=False, unique=True, index=True)
    password = CharField(null=True)
    active = BooleanField(default=True)
    groups = ArrayField(CharField, default=[])
    connection = BinaryJSONField(null=True)  # {'provider': 'google', 'token': <token>}


class GroupUser(BaseModel):
    created = DateTimeField(default=datetime.datetime.now)
    ctx = IntegerField(default=0)
    user_id = ForeignKeyField(User, null=False, on_delete='CASCADE', db_column='user_id_id')
    group = CharField(null=False)
