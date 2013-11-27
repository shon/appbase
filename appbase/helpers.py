from base64 import b64encode
import hashlib
import random
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage

import html2text

import settings


def send_email(sender, recipient, subject, text=None, html=None, images=[]):
    """
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
    msg['To'] = recipient

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
    s.sendmail(msg['From'], msg['To'], msg.as_string())

    s.quit()


def gen_random_token():
    return b64encode(hashlib.sha256(str(random.getrandbits(256))).digest(),
                     random.sample(settings.SALT, 2)).rstrip('==')
