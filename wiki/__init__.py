import os

from flask import Flask, render_template
from flask_session import Session

import redis

from . import wiki

from beem import Hive
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
        SESSION_USE_SIGNER=True,
        DB_HOSTNAME='localhost',
        HIVE_INTERFACE="https://hive.blog",
        HIVE_NODE="https://api.hive.blog",
        START_PAGE='Welcome-To-Propolis-Wiki',
        EDIT_GUIDELINES='How-To-Edit-Propolis-Wiki'
    )

    app.config.from_pyfile('config.py')
    app.config['SESSION_REDIS'] = redis.from_url(app.config['SESSION_REDIS'])
    app.secret_key = app.config['SECRET_KEY']

    app.client = Hive(keys=[app.config['ACTIVE_KEY'],app.config['POSTING_KEY']], node=app.config['HIVE_NODE'])

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html")

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    wiki.bp.register_blueprint(hive_keychain_auth)
    app.register_blueprint(wiki.bp)

    server_session = Session(app)

    return app