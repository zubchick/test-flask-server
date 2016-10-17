# coding: utf-8
from contextlib import contextmanager
import logging
from time import sleep

from flask import Flask
from flask import request
from flask import Response

import requests
from werkzeug.contrib.cache import MemcachedCache

app = Flask(__name__)
cache = MemcachedCache(['127.0.0.1:11211'])
session = requests.Session()
log = logging.getLogger(__name__)

logging.basicConfig(
    format='[%(process)d] %(levelname)s %(asctime)s %(message)s',
    level=logging.DEBUG,
)


@app.route("/", methods=['GET'])
def hello():
    key = request.args['key']
    return Response(
        response=get_key(key),
        status=200,
        mimetype="application/json"
    )


def get_key(key):
    value = cache.get(key)
    refreshed = False

    if value is None:
        with lock(key):
            # optimization
            value = cache.get(key)

            if value is None:
                value = refresh_key(key)
                refreshed = True

    if not refreshed:
        log.debug('Get key %s from cache', key)

    return str(value)


def refresh_key(key):
    log.debug('Refresh key %s', key)

    while True:
        try:
            result = session.get('https://vast-eyrie-4711.herokuapp.com/?',
                                 params={'key': key})
        except requests.RequestException, exc:
            log.warning('Connection exception %s', exc)
            continue

        if result.ok:
            value = result.content
            cache.set(key, value, timeout=24 * 3600)
            log.debug('Add key %s to cache', key)
            return value
        else:
            log.warning(
                'Server responded with error %s for key %s',
                result.status_code,
                key
            )


@contextmanager
def lock(key, timeout=60):
    """ Acquire lock.

    If lock have already acquired then whait.

    """
    lock_name = 'lock:' + key
    log.debug('Trying lock %s.', lock_name)

    if cache.get(lock_name) is not None:
        log.debug('Lock %s is acuired. Wait.', lock_name)
        while cache.get(lock_name) is not None:
            sleep(0.1)

    try:
        cache.set(lock_name, 1, timeout=timeout)
        yield
    finally:
        cache.delete(lock_name)
