import datetime
import hashlib
import logging
import os.path
import re

from blinker import signal

import settings
import appbase.context as context
import appbase.helpers
import appbase.pw as pw
import playhouse.shortcuts
import appbase.redisutils as redisutils
import appbase.users.sessions as sessionslib
from appbase.errors import SecurityViolation
from appbase.users.model import User, GroupUser
from appbase.helpers import gen_random_token
from appbase.common import local_path
from .errors import EmailExistsError, InvalidEmailError, EmailiDoesNotExistError, \
    PasswordTooSmallError, InvalidTokenError, SendEmailError, AuthError

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
    template_path = 'templates/welcome.txt'
    if not os.path.exists(local_path(template_path)):
        return
    text = render_template(template_path, data)
    #html = render_template('users/templates/invite.html', data)
    #images = [('signature', open('users/templates/logo.png').read())]
    sender = settings.WELCOME_SENDER
    recipient = email
    subject = settings.WELCOME_SUBJECT
    appbase.helpers.send_email(sender, recipient, subject, text=text)
    return True


def invite(name, email):
    data = dict(NAME=name, INVITER_NAME=settings.INVITER_NAME, INVITE_LINK=settings.INVITE_LINK, INVITER_EMAIL=settings.INVITER_EMAIL)
    html = render_template('users/templates/invite.html', data)
    sender = '{INVITER_NAME} <{INVITER_EMAIL}>'.format(**data)
    appbase.helpers.send_email(sender, email, settings.INVITE_SUBJECT, html=html)
    return True


def signup(email, password, **kwargs):
    validate_password(password)
    if not validate_email(email):
        raise InvalidEmailError(email)
    email = email.lower()
    if uid_by_email(email):
        raise EmailExistsError(email)
    lookup_key = gen_signuploopkup_key(email)
    token = rconn.get(lookup_key)
    if not token:
        token = gen_random_token()
        key = gen_signup_key(token)
        rconn.set(lookup_key, token)
        rconn.expire(lookup_key, SIGNUP_TTL)
        d = dict(email=email, password=password)
        d.update(kwargs)
        rconn.hmset(key, d)
        rconn.expire(key, SIGNUP_TTL)
    confirmation_link = settings.CONFIRMATION_LINK.format(TOKEN=token)
    data = dict(CONFIRMATION_LINK=confirmation_link, SIGNUP_SENDER=settings.SIGNUP_SENDER, DOMAIN=settings.DOMAIN)
    html = render_template('templates/confirmation.html', data)
    try:
        appbase.helpers.send_email(settings.SIGNUP_SENDER, email, settings.SIGNUP_SUBJECT, html=html)
    except Exception:
        logging.exception('error while sending confirmation email: ')
        raise SendEmailError()
    return True


def complete_signup(token, groups=None):
    """
    Do not expose this function directly
    """
    key = gen_signup_key(token)
    data = rconn.hgetall(key)
    if not data:
        raise InvalidTokenError()
    if groups:
        data['groups'] = groups
    uid = create(**data)
    user = info(uid=uid)
    return sessionslib.create(uid, user['groups'])


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

def create(email, password=None, groups=None, name=None, connection=None):
    email = email.lower()

    if password:
        validate_password(password)
        if not validate_email(email):
            raise InvalidEmailError(email)
        encpassword = encrypt(password, settings.SALT)
    else:
        encpassword = None

    if uid_by_email(email):
        raise EmailExistsError(email)

    created = datetime.datetime.now()
    user = User.create(name=name, email=email, password=encpassword, created=created, groups=groups or [])
    user.save()

    if groups:
        for gname in groups:
            GroupUser.create(user_id=user.id, group=gname)
    #user_created.send(uid, email)
    if settings.SEND_WELCOME_EMAIL:
        welcome(email)
    return user.id


def info(email=None, uid=None):
    if email:
        cond = (User.email == email.lower())
    else:
        cond = (User.id == uid)
    user = User.select(User.name, User.id, User.active, User.created, User.groups).where(cond)[0]
    return playhouse.shortcuts.model_to_dict(user)


def authenticate(email, password='', _oauthed=False):
    """
    returns session if successful else returns None
    """
    if not validate_email(email):
        raise InvalidEmailError(email)
    user = User.get(User.email == email.lower())
    if not user:
        raise EmailiDoesNotExistError(email)
    if _oauthed:
        return sessionslib.create(user.id, user.groups)
    if user.password == encrypt(password, settings.SALT):
        return sessionslib.create(user.id, user.groups)
    raise AuthError(email)


def set_user_context(uid=None, email=None):
    if email:
        user = User.get(User.email == email.lower())
    else:
        user = User.get(User.id == uid)
    sid = sessionslib.create(user.id, user.groups)
    context.set_context(uid=user.id, sid=sid, groups=user.groups)


def edit(uid, mod_data):
    editables = set(['name', 'email', 'password'])
    if not editables.issuperset(mod_data.keys()):
        raise SecurityViolation()
    if 'password' in mod_data:
        mod_data['password'] = encrypt(mod_data['password'], settings.SALT)
    q = Users.update(**mod_data).where(User.id == uid)
    q.execute()
    return True


def enable(uid):
    q = User.update(active=True).where(User.id == uid)
    q.execute()


def disable(uid):
    q = User.update(active=False).where(User.id == uid)
    q.execute()


def uid_by_email(email):
    """
    -> user or None
    """
    user = User.select(User.id).where(User.email == email.lower()).first()
    if user:
        return user.id

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
    fields = [User.id, User.email, User.active, User.created, User.groups]
    return list(User.select(*fields))
