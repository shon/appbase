from appbase.errors import BaseError


class EmailExistsError(BaseError):
    def __init__(self, email):
        self.msg = 'Account with email "{email}" exists'.format(email=email)
        self.data = {'email': email}


class InvalidEmailError(BaseError):
    def __init__(self, email):
        self.msg = 'Invalid email: {email}'.format(email=email)
        self.data = {'email': email}


class AuthError(BaseError):
    def __init__(self, email):
        self.msg = 'Authentication failed'
        self.data = {'email': email}
