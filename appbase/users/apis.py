import hashlib

from sqlalchemy.sql import select, func

import settings
import appbase.helpers
import appbase.sa as sa
import appbase.redisutils as redisutils
import appbase.users.sessions as sessionslib
from appbase.errors import SecurityViolation
from appbase.users.schema import users
from appbase.helpers import gen_random_token

SIGNUP_KEY_PREFIX = 'invite:'
SIGNUP_TTL = 2 * 7 * 24 * 60 * 60
rconn = redisutils.rconn


def gen_signup_key(email):
    return SIGNUP_KEY_PREFIX + email


def welcome(email, data={}):
    text_tmpl = open('users/templates/welcome.txt').read()
    text = text_tmpl.format(data)
    #html_tmpl = open('users/templates/welcome.html').read()
    #html = html_tmpl.format(data)
    #images = [('signature', open('users/templates/logo.png').read())]
    sender = settings.WELCOME_SENDER
    recipient = email
    subject = settings.WELCOME_SUBJECT
    appbase.helpers.send_email(sender, recipient, subject, text)
    return True


def invite(name, email):
    data = dict(NAME=name, INVITER_NAME=settings.INVITER_NAME, INVITE_LINK=settings.INVITE_LINK)
    html_tmpl = open('users/templates/invite.html').read()
    html = html_tmpl.format(data)
    sender = '{INVITER_NAME} <{INVITER_EMAIL}>'.format(INVITER_NAME=INVITER_NAME, INVITER_EMAIL=INVITER_EMAIL)
    appbase.helpers.send_email(sender, recipient, subject, html=html)
    return True


def signup(fname, lname, email, password):
    token = gen_random_token()
    key = gen_signup_key(token)
    d = dict(fname=fname, lname=lname, email=email, password=password)
    rconn.hmset(key, d)
    rconn.expire(key, SIGNUP_TTL)
    return True


def complete_signup(token):
    key = gen_signup_key(token)
    data = rconn.hmget(key)
    return create(**data)


def encrypt(s, salt=''):
    h = hashlib.sha256()
    h.update(s + salt)
    return h.hexdigest()


def create(fname, lname, email, password, groups=[], connection=None):
    conn = sa.connect()
    encpassword = encrypt(password, settings.SALT)
    q = users.insert().values(fname=fname, lname=lname, email=email, password=encpassword)
    conn.execute(q)
    q = select([users.c.id]).where(users.c.email == email)
    return conn.execute(q).fetchone()[0]


def list():
    conn = sa.connect()
    q = users.select()
    return conn.execute(q).fetch_all()


def authenticate(email, password):
    """
    returns session if successful else returns None
    """
    conn = sa.connect()
    q = select([users.c.id, users.c.password]).where(users.c.email == email)
    uid, encpassword = conn.execute(q).fetchone()
    if encpassword == encrypt(password, settings.SALT):
        return sessionslib.create(uid)


def edit(uid, mod_data):
    conn = sa.connect()
    editables = set('fname', 'lname', 'email', 'password')
    if not editables.issuperset(mod_data.keys()):
        raise SecurityViolation()
    if 'password' in mod_data:
        mod_data['password'] = encrypt(password)
    q = users.update().values(**mod_data).where(users.c.id == uid)
    conn.execute(q)
    raise NotImplemented


def enable(uid):
    conn = sa.connect()
    q = users.update().values(active=True).where(users.c.id == uid)
    conn.execute(q)


def disable(uid):
    conn = sa.connect()
    q = users.update().values(active=False).where(users.c.id == uid)
    conn.execute(q)


def count():
    conn = sa.connect()
    q = select([func.count(users.c.id)])
    return conn.execute(q).fetchone()[0]


def request_reset_password(uid):
    raise NotImplemented


def reset_password(token, password):
    raise NotImplemented


def remove(uid):
    raise NotImplemented


def archive():
    raise NotImplemented


def bulkcreate():
    raise NotImplemented


def import_data():
    raise NotImplemented
