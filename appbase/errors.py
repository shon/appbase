class BaseError(Exception):
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
    def to_dict(self):
        return {'msg': getattr(self, 'msg', ''),
                'code': getattr(self, 'code', None),
                'data': getattr(self, 'data', {})}


class SecurityViolation(BaseError): pass
