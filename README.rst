Tests
=====

::
    # Start fake smtp server
    python -m smtpd -n -c DebuggingServer localhost:10000
    # OR python tests/fakemail.py --port 10000  # saves to .eml file in cwd

    # Create your settings.py
    cp settings-available/dev.py settings.py

    # run tests
    nosetests -xv tests
