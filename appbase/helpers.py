from base64 import b64encode
import hashlib
import random
import smtplib
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
if sys.version[0] == '2':
    from email.MIMEImage import MIMEImage
else:
    from email.mime.image import MIMEImage

import html2text

import settings
import appbase.context as context
from appbase.errors import AccessDenied


def send_email(sender, recipient, subject, text=None, html=None, images=[], reply_to=None, bcc=None):
    """
    recipient: email string or list of email strings
    text: text message. If html is provided and not text, text will be auto generated
    html: html message
    images: list of cid and image paths. eg. [('logo', 'images/logo.png'), ('Bruce', 'images/bat.png')]
    """
    assert any((text, html)), 'please provide html or text'

    if html and not text:
        text = html2text.html2text(html)

    msg = MIMEMultipart('alternative')

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipient) if isinstance(recipient, list) else recipient
    if bcc:
        msg['bcc'] = bcc
    if reply_to:
        msg.add_header('reply-to', reply_to)

    msg.attach(MIMEText(text, 'plain', 'utf-8'))
    if html:
        msg.attach(MIMEText(html, 'html', 'utf-8'))
    for cid, img in images:
        img_part = MIMEImage(img)
        img_part.add_header('Content-ID', '<' + cid + '>')
        msg.attach(img_part)

    s = smtplib.SMTP(settings.MD_HOST, settings.MD_PORT)
    if settings.MD_USERNAME:
        s.login(settings.MD_USERNAME, settings.MD_KEY)
    #s.set_debuglevel(1)
    s.sendmail(msg['From'], msg['To'], msg.as_string())

    s.quit()


def gen_random_token():
    return b64encode(
        hashlib.sha256(str(random.getrandbits(256)).encode()).digest(),
        ''.join(random.sample(settings.SALT, 2)).encode()
        ).decode().rstrip('==')


def make_key_from_params(fname, args, kw={}, seperator=':', strict=True):
    """
    Generates a unique key of params and function name.

    seperator - Any unique string to seperate args and kwds.
    strict - If strict True, unhashable types like list are filtered.
    """
    key = (fname,) + args + (seperator,)
    for item in kw.items():
        key += item
    if strict:
        key = tuple(filter(lambda x: isinstance(x, (int, str, bool, float, tuple, frozenset)), key))
    return key


def notify_dev(trace, f_name, now):
    sender = settings.DEV_EMAIL
    recipient = settings.DEV_EMAIL
    subject = 'Alert | Error in %s [%s]' % (f_name, now)
    text = trace
    send_email(sender, recipient, subject, text)


def match_roles(required_roles, op, **kw):
    req_roles = set(role.format(**kw) for role in required_roles)
    user_roles = set(context.current.groups)
    if op == 'any' and user_roles.isdisjoint(req_roles):
        raise AccessDenied(
            data=dict(groups=user_roles, roles_required=req_roles)
        )
    elif op == 'all' and not user_roles.issuperset(req_roles):
        raise AccessDenied(
            data=dict(groups=user_roles, roles_required=req_roles)
        )


def match_any_role(required_roles, **kw):
    match_roles(required_roles, 'any', **kw)


def match_all_roles(required_roles, **kw):
    match_roles(required_roles, 'all', **kw)
