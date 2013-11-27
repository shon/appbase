DEBUG = True

LOCALDIR = 'tests/localdir'
SALT = 'PLEASE_CHANGE'
DB_NAME = 'devdb'
DB_URL = 'postgres:///' + DB_NAME

# Redis
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_SESSIONS_DB = 1

# users
WELCOME_SENDER = 'Welcome <welcome@example.com>'
WELCOME_SUBJECT = 'Welcome to Appbase'
INVITER_NAME = ''
INVITE_LINK = ''
INVITER_EMAIL = ''
SIGNUP_SUBJECT = 'Appbase: Please cofirm signup'
SIGNUP_SENDER = 'no-reply@example.com'
CONFIRMATION_LINK = 'https://example.com/confirm/{TOKEN}'

# Mail
MD_HOST = '127.0.0.1'
MD_PORT = '10000'
MD_USERNAME = None
