import datetime

from sqlalchemy.sql import select, func

import appbase.sa as sa
from appbase.users.schema import users


def count():
    conn = sa.connect()
    q = select([func.count(users.c.id)])
    return conn.execute(q).fetchone()[0]


def groupby_created(precision='month'):
    conn = sa.connect()
    month = func.date_trunc('month', users.c.created).label('month')
    q = select([month, func.count(users.c.id)]).group_by('month').order_by('month')
    #return conn.execute(q).fetchall()
    return [(dt.strftime('%b %Y'), num) for (dt, num) in conn.execute(q).fetchall()]


def created_today():
    conn = sa.connect()
    today = datetime.date.today()
    q = select([func.count(users.c.id)]).where(users.c.created > today)
    return conn.execute(q).fetchone()[0]
