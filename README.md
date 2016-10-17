test server
===========

----------
How to run
----------

0. Install and run `memcached` on `127.0.0.1:11211`
1. `pip install -r requirements.txt`
2. `gunicorn -w 4 -b 127.0.0.1:5000 app:app --timeout=60`
3. Test `curl 'http://127.0.0.1:5000/?key=1234567' --max-time 1`
