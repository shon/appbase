import os
from requests_oauthlib import OAuth2Session

import appbase.users.apis as userapis

import settings


if not settings.G_REDIRECT_URI.startswith('https'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'True'

# http://example.com/?state=QjaZneV6q1Lw1PDeGkIBpGN6zGFGD1&code=4/izHiQ5fkIYLJ-CHaKO-sHLZphAZ1oLCWTB0kZSYQPMc#
#
# {
#      "id": "101040630350628241843",
#      "email": "someone@example.com",
#      "verified_email": true,
#      "name": "Fname Lname",
#      "given_name": "Fname",
#      "family_name": "Lname",
#      "picture": "https://lh6.googleusercontent.com/-ROwm2oX4xQ0/AAAAAAAAAAI/AAAAAAAAAAA/7aSyJfrQWf0/photo.jpg",
#      "locale": "en",
#      "hd": "example.com"
# }

def get_signup_url():
    authorization_base_url = "https://accounts.google.com/o/oauth2/auth"
    google = OAuth2Session(settings.G_CLIENT_ID, scope=settings.G_SCOPE, redirect_uri=settings.G_REDIRECT_URI)
    authorization_url, state = google.authorization_url(authorization_base_url, access_type='online', approval_prompt='force')
    return authorization_url


def login(token=None, authorization_response=None):
    """
    returns session_id, info
    info: {name: name, email: email}
    """
    if not token:
        google = OAuth2Session(settings.G_CLIENT_ID, scope=settings.G_SCOPE, redirect_uri=settings.G_REDIRECT_URI)
        token_url = "https://accounts.google.com/o/oauth2/token"
        token = google.fetch_token(token_url, client_secret=settings.G_CLIENT_SECRET, authorization_response=authorization_response)
    google = OAuth2Session(settings.G_CLIENT_ID, token=token)
    ginfo = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
    email = ginfo['email']
    uid = userapis.uid_by_email(email)
    if not uid:
        uid = userapis.create(name=ginfo['name'], email=email, connection={'provider': 'google', 'token': token})
    userinfo = {'name': ginfo['name'], 'email': ginfo['email'], 'id': uid}
    return userapis.authenticate(email=ginfo['email'], _oauthed=True), userinfo


def update(email, mod_data):
    """
    mod_data: {name: <name>}
    """
    return userapis.update(name=name)
