import datetime
import hashlib
import re

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
from .errors import EmailExistsError, InvalidEmailError, EmailiDoesNotExistError, PasswordTooSmallError

SIGNUP_KEY_PREFIX = 'signup:'
SIGNUP_LOOKUP_PREFIX = 'signuplookup:'
SIGNUP_TTL = 2 * 7 * 24 * 60 * 60
PASSWORD_RESET_TTL = 24 * 60 * 60
rconn = redisutils.rconn

user_created = signal('user.created')

qtext = '[^\\x0d\\x22\\x5c\\x80-\\xff]'
dtext = '[^\\x0d\\x5b-\\x5d\\x80-\\xff]'
atom = '[^\\x00-\\x20\\x22\\x28\\x29\\x2c\\x2e\\x3a-\\x3c\\x3e\\x40\\x5b-\\x5d\\x7f-\\xff]+'
quoted_pair = '\\x5c[\\x00-\\x7f]'
domain_literal = "[\\x5b](?:%s|%s)*[\\x5d]" % (dtext, quoted_pair)
quoted_string = "\\x22(?:%s|%s)*\\x22" % (qtext, quoted_pair)
domain_ref = atom
sub_domain = "(?:%s|%s)" % (domain_ref, domain_literal)
word = "(?:%s|%s)" % (atom, quoted_string)
domain = "%s(?:\\x2e%s)*" % (sub_domain, sub_domain)
local_part = "%s(?:\\x2e%s)*" % (word, word)
# Adding maximum length restrictions
addr_spec = "(?=^.{1,256}$)(?=.{1,64}@)%s\\x40%s" % (local_part, domain)
email_address = re.compile('^%s$' % addr_spec)


def validate_email(email):
    return email and email_address.match(email)

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


# Placeholder code: should be replaced with proper validation decorator

password_schema = {'type': 'string', 'minLength': 5}
user_schema = {'type': 'object',
               'properties': {
                   'password': password_schema }
               }

from jsonschema import Draft4Validator

def validate_password(password):
    v = Draft4Validator(password_schema)
    e = list(v.iter_errors(password))
    if e and e[0].message.endswith('is too short'):
        raise PasswordTooSmallError()

# /Placeholder code

def create(fname, lname, email, password, groups=[], connection=None, _welcome=True):
    validate_password(password)
    if not validate_email(email):
        raise InvalidEmailError(email)
    email = email.lower()
    if uid_by_email(email):
        raise EmailExistsError(email)
    conn = sa.connect()
    encpassword = encrypt(password, settings.SALT)
    created = datetime.datetime.now()
    q = users.insert().values(fname=fname, lname=lname, email=email, password=encpassword, created=created)
    conn.execute(q)
    q = select([users.c.id]).where(users.c.email == email)
    uid = conn.execute(q).fetchone()[0]
    #user_created.send(uid, fname, lname, email)
    return uid


def info(email):
    conn = sa.connect()
    _fields = [users.c.id, users.c.fname, users.c.lname, users.c.active, users.c.created]
    q = select(_fields).where(users.c.email == email.lower())
    res = conn.execute(q)
    return dict(zip(res.keys(), res.fetchone()))


def authenticate(email, password):
    """
    returns session if successful else returns None
    """
    if not validate_email(email):
        raise InvalidEmailError(email)
    conn = sa.connect()
    q = select([users.c.id, users.c.password]).where(users.c.email == email.lower())
    row = conn.execute(q).fetchone()
    if not row:
        raise EmailiDoesNotExistError(email)
    uid, encpassword = conn.execute(q).fetchone()
    if encpassword == encrypt(password, settings.SALT):
        return sessionslib.create(uid)


def edit(uid, mod_data):
    conn = sa.connect()
    editables = set(['fname', 'lname', 'email', 'password'])
    if not editables.issuperset(mod_data.keys()):
        raise SecurityViolation()
    if 'password' in mod_data:
        mod_data['password'] = encrypt(mod_data['password'], settings.SALT)
    q = users.update().values(**mod_data).where(users.c.id == uid)
    conn.execute(q)
    return True


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
    q = select([users.c.id]).where(users.c.email == email.lower())
    row = conn.execute(q).fetchone()
    return row and row[0] or None

PASSRESET_PREFIX = 'passreset:'



def request_reset_password(email):
    existing_keys = rconn.get(PASSRESET_PREFIX + email + '*')
    if not existing_keys:
        token = gen_random_token()
        key = '{prefix}{email}:{token}'.format(prefix=PASSRESET_PREFIX, email=email, token=token)
        key = existing_keys[0]
        rconn.set(key, '')
        rconn.expire(key, PASSWORD_RESET_TTL)
    else:
        key = existing_keys[0]
        token = key.split(':')[-1]
    reset_link = settings.PASSWORD_RESET_LINK.format(TOKEN=token)
    data = dict(PASSWORD_RESET_LINK=reset_link, SENDER=settings.RESET_PASSWORD_SENDER)
    html = render_template('users/templates/password_reset.html', data)
    appbase.helpers.send_email(settings.SIGNUP_SENDER, email, 'Password reset', html=html)
    return True


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


def list_():
    conn = sa.connect()
    q = users.select()
    return conn.execute(q).fetch_all()
