import os

from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

try:
    from converge import settings
except Exception as err:
    import settings

authorization_base_url = 'https://www.facebook.com/dialog/oauth'
token_url = 'https://graph.facebook.com/oauth/access_token'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'


def create_fb_session():
    session = OAuth2Session(settings.FB_APP_ID,
                            redirect_uri=settings.FB_RETURN_URL,
                            scope=settings.FB_SCOPE)
    return facebook_compliance_fix(session)


def get_auth_url():
    # Redirect user to Facebook for authorization
    session = create_fb_session()
    authorization_url, state = session.authorization_url(authorization_base_url)
    return authorization_url


def connect(authorization_response=None):
    """
    accepts authorization_response/token and creates user login for that user
    token: token dict which returned by fb sdk on session.fetch_token
    returns session_id, info
        (info: {name: name, email: email})
    """
    session = create_fb_session()
    token = session.fetch_token(token_url,
                                client_secret=settings.FB_APP_SECRET,
                                auth=False,
                                authorization_response=authorization_response)
    info_url = 'https://graph.facebook.com/me?fields=' + settings.FB_USER_FIELDS
    return token, session.get(info_url).json()


def fetch_info(access_token):
    session = OAuth2Session(token={'access_token': access_token})
    info_url = 'https://graph.facebook.com/me?fields=' + settings.FB_USER_FIELDS
    return session.get(info_url).json()
