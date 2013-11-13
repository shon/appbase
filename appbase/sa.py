import datetime

from sqlalchemy import create_engine, MetaData, Column, Integer, DateTime, BOOLEAN
from gevent.local import local

import settings

engine = create_engine(settings.DB_URL, convert_unicode=True, echo=True)
metadata = MetaData()


def connect():
    return local.saconn


def Column_created():
    return Column('created', DateTime, default=datetime.datetime.now)


def Column_id():
    return Column('id', Integer, primary_key=True)


def Column_active():
    return Column('active', BOOLEAN, default=True)


def tr_start(tls):
    conn = engine.connect()
    trans = conn.begin()
    tls.saconn = conn
    tls.satrans = trans


def tr_complete(tls):
    tls.satrans.commit()
    tls.saconn.close()


def tr_abort(tls):
    tls.satrans.rollback()
    tls.saconn.close()
