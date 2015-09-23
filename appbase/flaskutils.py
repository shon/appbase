import datetime
import decimal
import json
from flask import make_response, request, current_app, Response
from flask.json import JSONEncoder
from functools import update_wrapper
import settings

def crossdomain(origin=None, methods=None, headers=None,
                max_age=10368000, attach_to_all=True,
                automatic_options=True):
    # http://flask.pocoo.org/snippets/56/
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, datetime.timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is None:
                h['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '')
            else:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def jsonify_unsafe(o):
    extra_params = dict(sort_keys=True, indent=4, separators=(',', ': ')) if settings.ENV == 'dev' else {}
    return Response(json.dumps(o, cls=CustomJSONEncoder, **extra_params), mimetype='application/json')


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            elif isinstance(obj, decimal.Decimal):
                return float(obj)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def support_datetime_serialization(app):
    app.json_encoder = CustomJSONEncoder
    return app


def add_cors_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Max-Age'] = '10368000'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS, PATCH'
    resp.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '')
