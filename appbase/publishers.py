import urllib
from functools import wraps
import json
import random

from flask import request, jsonify, make_response

from appbase.flaskutils import support_datetime_serialization, add_cors_headers, jsonify_unsafe
import appbase.pw as db
import settings
from appbase.errors import BaseError, AccessDenied
import appbase.users.sessions as sessionlib
import appbase.context as context


def flaskapi(app, f):
    @wraps(f)
    def wrapper(*args, **kw):
        context.current.uid = 0
        context.current.groups = []
        session_id = request.cookies.get('session_id')
        if session_id:
            if request.environ['REQUEST_METHOD']:
                session_id = urllib.unquote(session_id)
            context.current.sid = session_id
        status_code = 200
        if request.method == 'OPTIONS':
            resp = app.make_default_options_response()
        else:
            kw.update(request.json or (request.data and json.loads(request.data)) or request.form)
            try:
                result = f(*args, **kw)
            except AccessDenied as err:
                result = err.to_dict()
                status_code = 403
                app.logger.exception('Access Denied error: ')
            except BaseError as err:
                app.logger.exception('API Execution error: ')
                result = err.to_dict()
                status_code = 500
            except Exception as err:
                err_id = str(random.random())[2:]
                app.logger.exception('Unhandled API Execution error [%s]: ', err_id)
                result = {'msg': ('Server error: ' + err_id)}
                status_code = 500
                kw_s = dict((k, str(v)[:50]) for (k, v) in kw.items())
                app.logger.error('[%s] parameters: %s', err_id, kw_s)
            if isinstance(result, dict):
                resp = jsonify(result)
            else:
                resp = make_response(jsonify_unsafe(result))
            resp.status_code = status_code
        add_cors_headers(resp)
        return resp
    return wrapper


def dbtransaction(f):
    def wrapper(*args, **kw):
        # with pw.db.transaction() ?
        db.tr_start()
        try:
            result = f(*args, **kw)
            db.tr_complete()
            return result
        except Exception as err:
            # TODO: log
            db.tr_abort()
            raise
    return wrapper


def protected(f):
    roles_required = getattr(f, 'roles_required', None)
    if not roles_required: return f
    def wrapper(*args, **kw):
        session_id = kw.pop('_session_id', None) or hasattr(context.current, 'sid') and context.current.sid
        if not session_id:
            raise AccessDenied(msg='session not found')
        uid, groups = sessionlib.sid2uidgroups(session_id)
        context.set_context(sid=session_id, uid=uid, groups=groups)
        if not set(context.current.groups).intersection(roles_required):
            raise AccessDenied(data=dict(groups=groups, roles_required=roles_required))
        return f(*args, **kw)
    return wrapper


def add_url_rule(app, url, handler, methods):
    # add debugging, inspection here
    print('%s -> %s [%s]' % (url, handler, str(methods)))
    if not 'OPTIONS' in methods:
        methods.append('OPTIONS')
    endpoint = url + '-' + str(methods)
    f = flaskapi(app, protected(dbtransaction(handler)))
    app.add_url_rule(url, endpoint, f, methods=methods)


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
        collection_url = self.urls_prefix + url
        resource_url = collection_url + '<' + id_type + ':' + id_name + '>'

        if isinstance(handlers, dict):
            raise NotImplemented
        elif isinstance(handlers, (list, tuple)):
            get_collection, add_resource, get_resource, edit_resource, delete_resource = handlers
        else:
            raise NotImplemented

        if get_collection:
            add_url_rule(self.app, collection_url, get_collection, methods=['GET'])
        if add_resource:
            add_url_rule(self.app, collection_url, add_resource, methods=['POST'])
        if get_resource:
            add_url_rule(self.app, resource_url, get_resource, methods=['GET'])
        if edit_resource:
            add_url_rule(self.app, resource_url, edit_resource, methods=['PUT'])
        if delete_resource:
            add_url_rule(self.app, resource_url, delete_resource, methods=['DELETE'])


class HTTPPublisher(object):
    """
    Expose functions/callables over HTTP.
    """
    def __init__(self, flask_app, api_urls_prefix='/api/'):
        self.app = flask_app
        self.urls_prefix = api_urls_prefix

    def add_mapping(self, url, handler, methods=['GET']):
        """
        Add a mapping for a callable.
        """
        url = self.urls_prefix + url
        add_url_rule(self.app, url, handler, methods=methods)
