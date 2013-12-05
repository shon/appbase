import datetime
import hashlib

from blinker import signal
from sqlalchemy.sql import select, func

import settings
import appbase.helpers
import appbase.sa as sa
import appbase.redisutils as redisutils
import appbase.users.sessions as sessionslib
from appbase.errors import SecurityViolation
from appbase.users.schema import users
from appbase.helpers import gen_random_token
from appbase.common import local_path

SIGNUP_KEY_PREFIX = 'signup:'
SIGNUP_LOOKUP_PREFIX = 'signuplookup:'
SIGNUP_TTL = 2 * 7 * 24 * 60 * 60
rconn = redisutils.rconn

user_created = signal('user.created')


def gen_signup_key(token):
    return SIGNUP_KEY_PREFIX + token


def gen_signuploopkup_key(email):
    return SIGNUP_LOOKUP_PREFIX + email


def signupemail2token(email):
    key = gen_signuploopkup_key(email)
    return rconn.get(key)


def render_template(path, data):
    path = local_path(path)
    tmpl = open(path).read()
    return tmpl.format(**data)


def welcome(email, data={}):
    text = render_template('users/templates/welcome.txt', data)
    #html = render_template('users/templates/invite.html', data)
    #images = [('signature', open('users/templates/logo.png').read())]
    sender = settings.WELCOME_SENDER
    recipient = email
    subject = settings.WELCOME_SUBJECT
    appbase.helpers.send_email(sender, recipient, subject, text)
    return True


def invite(name, email):
    data = dict(NAME=name, INVITER_NAME=settings.INVITER_NAME, INVITE_LINK=settings.INVITE_LINK)
    html = render_template('users/templates/invite.html', data)
    sender = '{INVITER_NAME} <{INVITER_EMAIL}>'.format(INVITER_NAME=INVITER_NAME, INVITER_EMAIL=INVITER_EMAIL)
    appbase.helpers.send_email(sender, recipient, subject, html=html)
    return True


def signup(fname, lname, email, password):
    lookup_key = gen_signuploopkup_key(email)
    token = rconn.get(lookup_key)
    if not token:
        token = gen_random_token()
        key = gen_signup_key(token)
        rconn.set(lookup_key, token)
        rconn.expire(lookup_key, SIGNUP_TTL)
        d = dict(fname=fname, lname=lname, email=email, password=password)
        rconn.hmset(key, d)
        rconn.expire(key, SIGNUP_TTL)
    confirmation_link = settings.CONFIRMATION_LINK.format(TOKEN=token)
    data = dict(NAME=fname, CONFIRMATION_LINK=confirmation_link, SIGNUP_SENDER=settings.SIGNUP_SENDER)
    html = render_template('users/templates/confirmation.html', data)
    appbase.helpers.send_email(settings.SIGNUP_SENDER, email, settings.SIGNUP_SUBJECT, html=html)
    return True


def complete_signup(token):
    key = gen_signup_key(token)
    data = rconn.hgetall(key)
    return create(**data)


def encrypt(s, salt=''):
    h = hashlib.sha256()
    h.update(s + salt)
    return h.hexdigest()


def create(fname, lname, email, password, groups=[], connection=None, _welcome=True):
    conn = sa.connect()
    encpassword = _encpassword or encrypt(password, settings.SALT)
    create = datetime.datetime.now()
    q = users.insert().values(fname=fname, lname=lname, email=email, password=encpassword, created=created)
    conn.execute(q)
    q = select([users.c.id]).where(users.c.email == email)
    uid = conn.execute(q).fetchone()[0]
    #user_created.send(uid, fname, lname, email)
    return uid


def info(email):
    conn = sa.connect()
    _fields = [users.c.id, users.c.fname, users.c.lname, users.c.active, users.c.created]
    q = select(_fields).where(users.c.email == email)
    res = conn.execute(q)
    return dict(zip(res.keys(), res.fetchone()))


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


def uid_by_email(email):
    conn = sa.connect()
    q = select([users.c.id]).where(users.c.email == email)
    row = conn.execute(q).fetchone()
    return row and row[0] or None


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
