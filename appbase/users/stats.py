import datetime
import peewee

import appbase.pw as pw
from appbase.pwusers.model import User


def count():
    return User.select(peewee.fn.COUNT(User.id))


def groupby_created(precision='month'):
    conn = sa.connect()
    month = peewee.func.DATE_TRUNC('month', users.c.created).label('month')
    users = User.select([month, peewee.func.COUNT(User.id)]).group_by('month').order_by('month')
    return [(dt.strftime('%b %Y'), num) for (dt, num) in users]


def created_today():
    today = datetime.date.today()
    return User.select([peewee.fn.count(User.id)]).where(User.created > today)[0]
