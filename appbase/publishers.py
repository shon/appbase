import datetime
import json
import logging
import random
import sys

import settings

if sys.version[0] == '2':
    import urllib
    from functools32 import wraps, lru_cache
else:
    import urllib.parse as urllib
    from functools import wraps, lru_cache

from flask import request, jsonify, make_response, Response
from flask import current_app
from appbase.flaskutils import add_cors_headers, jsonify_unsafe
from appbase.errors import BaseError, AccessDenied, NotFoundError
from appbase.errors import InvalidSessionError
import appbase.users.sessions as sessionlib
import appbase.context as context

if settings.DB_TRANSACTIONS_ENABLED:
    from appbase.pw import dbtransaction
else:
    dbtransaction = lambda f: f

SESSION_COOKIE_NAME = getattr(settings, 'SESSION_COOKIE_NAME', '__s')

cache = lru_cache()
default_cache_ttl = datetime.timedelta(0, (10*60))


def extract_kw(request):
    return (request.args and dict((k, v) for (k, v) in request.args.items())) or \
            request.json or \
            (request.data and json.loads(request.data.decode('utf-8'))) or \
            request.form or \
            {}


def flaskapi(app, f, jsonify_result=True):
    @wraps(f)
    def wrapper(*args, **kw):
        logger = current_app.logger
        context.current.uid = 0
        context.current.groups = []
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id:
            if request.environ['REQUEST_METHOD']:
                session_id = urllib.unquote(session_id)
            context.current.sid = session_id
        status_code = 200
        if request.method == 'OPTIONS':
            resp = app.make_default_options_response()
        else:
            kw.update(extract_kw(request))
            try:
                result = f(*args, **kw)
            except AccessDenied as err:
                result = err.to_dict()
                status_code = 403
                logger.exception('Access Denied error: ')
            except NotFoundError as err:
                result = err.to_dict()
                status_code = err.code or 404
                logger.exception('Object not found error: ')
            except BaseError as err:
                logger.exception('API Execution error: ')
                result = err.to_dict()
                status_code = getattr(err, 'code', 500)
            except Exception as err:
                err_id = str(random.random())[2:]
                logger.exception('Unhandled API Execution error [%s]: ', err_id)
                result = {'msg': ('Server error: ' + err_id)}
                status_code = getattr(err, 'code', 500)
                logger.error('[%s] parameters: %s', err_id, str(kw)[:400])
            if isinstance(result, dict):
                resp = jsonify(result)
            elif isinstance(result, Response):
                resp = result
                status_code = resp.status_code
            else:
                result = jsonify_unsafe(result) if jsonify_result else result
                resp = make_response(result)
            resp.status_code = status_code
        #add_cors_headers(resp)
        return resp
    return wrapper


def protected(f):
    @wraps(f)
    def wrapper(*args, **kw):
        session_id = kw.pop('_session_id', None) or hasattr(context.current, 'sid') and context.current.sid
        session_required = getattr(f, 'session_required', None)
        login_required = getattr(f, 'login_required', None)
        roles_required = getattr(f, 'roles_required', None)

        if  session_required or login_required or roles_required:
            if session_id:
                uid, groups = sessionlib.sid2uidgroups(session_id)
            else:
                raise AccessDenied(msg='session not found')
        elif session_id:
            try:
                uid, groups = sessionlib.sid2uidgroups(session_id)
            except InvalidSessionError:
                uid, groups = None, []
        else:
            uid, groups = None, []
        context.set_context(sid=session_id, uid=uid, groups=groups)

        if login_required and not uid:
            raise AccessDenied(msg='login required')
        if roles_required and not set(context.current.groups).intersection(roles_required):
            raise AccessDenied(data=dict(groups=groups, roles_required=roles_required))

        return f(*args, **kw)
    return wrapper


def cached(f):
    if hasattr(f, 'cache'):
        cf = cache(f)
        cf.began = datetime.datetime.now()
        # checks if the function has 'cache_ttl' attribute which stores a specific cache expiry time for it,
        # else uses the default cache_ttl
        cache_ttl = getattr(f, 'cache_ttl', default_cache_ttl)
        @wraps(f)
        def wrapper(*args, **kw):
            now = datetime.datetime.now()
            if (now - cf.began) > cache_ttl:
                cf.cache_clear()
                cf.began = now
            return cf(*args, **kw)
        wrapper.cache_info = cf.cache_info
        return wrapper
    return f


def api_factory(handler):
    return protected(cached(dbtransaction(handler)))


def add_url_rule(app, url, handler, methods, jsonify_result=True):
    # add debugging, inspection here
    print('%s -> %s %s' % (url, handler, str(methods)))
    if not 'OPTIONS' in methods:
        methods.append('OPTIONS')
    endpoint = url + '-' + str(methods)
    f = flaskapi(app, api_factory(handler), jsonify_result=jsonify_result)
    app.add_url_rule(url, endpoint, f, methods=methods)


def get_or_not_found(f):
    @wraps(f)
    def wrapper(*args, **kw):
        ret = f(*args, **kw)
        if ret is None:
            raise NotFoundError()
        return ret
    return wrapper


class RESTPublisher(object):
    """
    Expose a generic Python module as a RESTful service.
    This uses Flask, a micro-framework to expose required methods/functions.
    Current implementation does not implement partial edit or support for
    HTTP PATCH
    """
    def __init__(self, flask_app, api_urls_prefix='/api/'):
        """
        Initialized with an instance of flask app, uuid_type and api url prefix
        uuid_type denotes the type used by the resource as uuid
        e.g. int or str
        """
        self.app = flask_app
        self.urls_prefix = api_urls_prefix

    def map_resource(self, url, handlers, resource_id=('string', 'id')):
        """
        Maps a resource and its methods to URLs.
        All handlers are not required and may be passed as None
        handlers can be
            - object with http verbs as method names
                class Todos:
                    def get():
                    def post():
                class Todo:
                    def get():
                    def put():
                    def delete():
                todo_collection = Todos()
                todo_resource = Todo()
            - verb to function map
                {get: get_todo, post: create_todo}
            - list/tuple of functions handling http methods
                (get_todo, create_todo, ..)
        """
        id_type, id_name = resource_id
        collection_url = (self.urls_prefix + url) if not url.startswith('/') else url
        resource_url = collection_url + '<' + id_type + ':' + id_name + '>'

        if isinstance(handlers, (list, tuple)):
            get_collection, add_resource, replace_resource, get_resource, edit_resource, delete_resource = handlers
        else:
            raise NotImplemented

        if get_collection:
            add_url_rule(self.app, collection_url, get_collection, methods=['GET'])
        if add_resource:
            add_url_rule(self.app, collection_url, add_resource, methods=['POST'])
        if replace_resource:
            add_url_rule(self.app, collection_url, replace_resource, methods=['PUT'])
        if get_resource:
            get_resource_wrapped = get_or_not_found(get_resource)
            add_url_rule(self.app, resource_url, get_resource_wrapped, methods=['GET'])
        if edit_resource:
            add_url_rule(self.app, resource_url, edit_resource, methods=['PATCH'])
        if delete_resource:
            add_url_rule(self.app, resource_url, delete_resource, methods=['DELETE'])


class HTTPPublisher(object):
    """
    Expose functions/callables over HTTP.
    """
    def __init__(self, flask_app, api_urls_prefix='/api/'):
        self.app = flask_app
        self.urls_prefix = api_urls_prefix

    def add_mapping(self, url, handler, methods=['GET'], jsonify_result=True):
        """
        Add a mapping for a callable.
        """
        url = (self.urls_prefix + url) if not url.startswith('/') else url
        add_url_rule(self.app, url, handler, methods=methods, jsonify_result=jsonify_result)
        print('%s -> %s' % (url, handler))
