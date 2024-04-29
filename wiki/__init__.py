import os

from flask import Flask
from flask_session import Session

import redis

from . import wiki

from .hive_keychain_auth.auth import hive_keychain_auth

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        WIKI_USER='wikiuser',
        POSTING_KEY='5Jnf...',
        ACTIVE_KEY='5JqE...',
        SESSION_TYPE='redis',
        SESSION_REDIS='redis://127.0.0.1:6379',
        SESSION_USE_SIGNER=True
    )

    app.config.from_pyfile('config.py')
    app.config['SESSION_REDIS'] = redis.from_url(app.config['SESSION_REDIS'])
    app.secret_key = app.config['SECRET_KEY']

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    wiki.bp.register_blueprint(hive_keychain_auth)
    app.register_blueprint(wiki.bp)

    server_session = Session(app)

    return app