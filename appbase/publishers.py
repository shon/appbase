from functools import wraps
import json

from gevent.local import local
from flask import abort, request, jsonify

import appbase.sa
import settings
from appbase.errors import BaseError


def add_cors_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Max-Age'] = '1728000'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS, PATCH'


def flaskapi(app, f):
    @wraps(f)
    def wrapper(*args, **kw):
        status_code = 200
        if request.method == 'OPTIONS':
            resp = app.make_default_options_response()
        else:
            kw.update(request.json or (request.data and json.loads(request.data)) or request.form)
            try:
                result = f(*args, **kw)
            except BaseError as err:
                app.logger.exception('API Execution error: ')
                result = err.to_dict()
                status_code = 500
            except Exception as err:
                app.logger.exception('Unhandled API Execution error: ')
                result = {}
                status_code = 500
                app.logger.error('parameters: %s', str(kw))
            resp = jsonify({'result': result})
        resp.status_code = status_code
        add_cors_headers(resp)
        return resp
    return wrapper


def satransaction(f):
    @wraps(f)
    def wrapper(*args, **kw):
        tls = local
        appbase.sa.tr_start(tls)
        try:
            result = f(*args, **kw)
            appbase.sa.tr_complete(tls)
            return result
        except Exception as err:
            # TODO: log
            appbase.sa.tr_abort(tls)
            raise
    return wrapper


def add_url_rule(app, url, handler, methods):
    # add debugging, inspection here
    print('%s -> %s [%s]' % (url, handler, str(methods)))
    methods.append('OPTIONS')
    app.add_url_rule(url, None, flaskapi(app, satransaction(handler)), methods=methods)


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
                    def post():
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
            add_url_rule(self.app, resource_url, edit_resource, methods=['POST'])
        if delete_resource:
            add_url_rule(self.app, resource_url, delete_resource, methods=['DELETE'])


class HTTPPublisher(object):
    """
    Expose some methods or functions over HTTP.
    """
    def __init__(self, flask_app):
        self.app = flask_app

    def add_mapping(self, url, handler, methods=['GET']):
        """
        Add a mapping for a callable.
        """
        add_url_rule(self.app, url, handler, methods=methods)
