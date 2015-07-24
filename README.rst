
=======
Appbase
=======

Collection of components to make Python web app development easier and more fun.

Problems 
========

Common problems appbase tries to solve

- Need of fetching request arguments
- Way to turn Python functions into HTTP/RESTish APIs
- Error handling and logging
- Input JSON validation
- Input conversion
- User and Role management json APIs
    - Auth
    - Only JSON APIs, no UI pages
- Rate limiting
- Host checks
- Configurable process model (gevent/threads)


Need of fetching request arguments
-----------------------------------

Usual flask code
~~~~~~~~~~~~~~~~~

.. code-block:: python

    app = Flask(__name__)
    
    @app.route('/foo')
    def bar():
        arg1 = request.args.get('arg1')
        arg2 = request.args.get('arg2')
        arg3 = request.args.get('arg3')
        do_something()

Above is tedious and is boring.

flask-reqarg
~~~~~~~~~~~~~~~~~

.. code-block:: python

    app = Flask(__name__)

    @app.route('/foo')
    def bar(arg1, arg2, arg3):
        do_something()

Above is much better code.. but do can we call bar() outside web request?

appbase
~~~~~~~~

.. code-block:: python

    def bar(arg1, arg2, arg3):
        do_something()

    app = Flask(__name__)

    http_publisher = appbase.publishers.HTTPPublisher(app)
    http_publisher.add_mapping('/bar/', add, ['POST'])
   

Existing solutions
~~~~~~~~~~~~~~~~~~

- flask-reqarg
    - http://jason2506.github.io/flask-reqarg
    - implicit
    - no convertors

- Webargs
    - https://webargs.readthedocs.org/en/latest/#hello-webargs
    - needs schema (not jsonschema)

- appbase
    - implicit
    - post/json to args


Ease of creating REST APIs
--------------------------
- No automatic API creation from ORM Model




REST API Creation::

    >>> import appbase.publishers

    >>> app = Flask(__name__)

    >>> rest_publisher = appbase.publishers.RESTPublisher(app)
    >>> handlers = (get_all, add_user, get_user, edit_user, delete_user)
    >>> rest_publisher.map_resource('users/', handlers, resource_id=('int', 'id'))


Proposals
=========

    >>> def foofunc():
    >>>     return 

    >>> foofunc.route = '/some/route'
    >>> foofunc.security = {groups: []}
    >>> foofunc.schema = {}

    >>> http_publisher = HTTPPublisher(app)
    >>> fooapi = http_publisher(foofunc)


Tests
=====

Running tests::

    # Start fake smtp server
    python -m smtpd -n -c DebuggingServer localhost:10000
    # OR python tests/fakemail.py --port 10000  # saves to .eml file in cwd

    # Create your settings.py
    cp settings-available/dev.py settings.py

    # run tests
    nosetests -xv tests
