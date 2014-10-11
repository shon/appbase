from appbase.errors import BaseError


class EmailExistsError(BaseError):
    def __init__(self, email):
        self.msg = 'Account with email "{email}" exists'.format(email=email)
        self.data = {'email': email}


class EmailiDoesNotExistError(BaseError):
    def __init__(self, email):
        self.msg = 'Invalid email address. Please try again.'
        self.data = {'email': email}


class InvalidEmailError(BaseError):
    def __init__(self, email):
        self.msg = 'Invalid email address. Please try again.'
        self.data = {'email': email}


class AuthError(BaseError):
    def __init__(self, email):
        self.msg = 'Incorrect password. Please try again.'
        self.data = {'email': email}


class PasswordTooSmallError(BaseError):
    def __init__(self):
        self.msg = 'Passwords must contain at least 5 characters.'


class InvalidTokenError(BaseError):
    def __init__(self):
        self.msg = 'Token is invalid or expired'
