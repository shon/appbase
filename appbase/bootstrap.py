import os
import logging
from logging.handlers import RotatingFileHandler
import sys


def use_gevent():
    import gevent.monkey
    gevent.monkey.patch_all()


def green_pg():
    import psycogreen.gevent
    psycogreen.gevent.patch_psycopg()


def check_settings(conf):
    settings_path = 'settings.py'
    dev_settings_path = 'settings-available/{0}.py'.format(conf)
    d = dict(dev_settings_path=dev_settings_path, settings_path=settings_path)
    if os.path.exists(settings_path):
        if not os.path.islink(settings_path):
            sys.exit('Error: {settings_path} is not a link. [hint: ln -s {dev_settings_path} {settings_path}]'.format(**d))
        else:
            os.remove(settings_path)
            os.symlink(d['dev_settings_path'], d['settings_path'])
    else:
        print('Warning: {settings_path} not found. [hint: ln -sf {dev_settings_path} {settings_path}]'.format(**d))
        os.symlink(d['dev_settings_path'], d['settings_path'])
    print('Using {dev_settings_path}'.format(**d))


def configure_logging(logger, name, debug=True):
    logdir = 'logs'
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logpath = os.path.join(logdir, name)
    file_handler = RotatingFileHandler(logpath, maxBytes=1024 * 1024 * 10, backupCount=100)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
