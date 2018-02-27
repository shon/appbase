import os

from requests_oauthlib import OAuth2Session

try:
    from converge import settings
except Exception as err:
    import settings

authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
token_url = 'https://accounts.google.com/o/oauth2/token'

if not settings.G_REDIRECT_URI.startswith('https'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'


def create_goo_session():
    session = OAuth2Session(settings.G_CLIENT_ID,
                            redirect_uri=settings.G_REDIRECT_URI,
                            scope=settings.G_SCOPE)
    return session


def get_auth_url():
    # Redirect user to Google for authorization
    session = create_goo_session()
    authorization_url, state = session.authorization_url(authorization_base_url, access_type='online')
    return authorization_url


def connect(authorization_response=None):
    """
    accepts authorization_response/token and creates user login for that user
    token: token dict which returned by fb sdk on session.fetch_token
    returns session_id, info
        (info: {name: name, email: email})
    """
    session = create_goo_session()
    token = session.fetch_token(token_url,
                                client_secret=settings.G_CLIENT_SECRET,
                                authorization_response=authorization_response)
    userinfo = session.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    return token, userinfo


def fetch_info(access_token):
    session = OAuth2Session(token={'access_token': access_token})
    userinfo = session.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    return userinfo
