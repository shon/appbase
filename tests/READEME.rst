Start fake mail server
----------------------
::
    
    python -m smtpd -n -c DebuggingServer localhost:10000
    # OR
    mkdir tests/tmp && python fakemail.py --port 10000 --path tmp

::

    nosetests -v tests --with-yanc --pdb-failures --pdb --with-time
