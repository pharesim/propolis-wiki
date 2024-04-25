import redis
from flask import Flask, Blueprint, request, session, render_template, redirect, url_for, jsonify
from flask_session import Session

from beem.account import Account
from beemgraphenebase.account import PublicKey
from beemgraphenebase.ecdsasig import verify_message

from binascii import hexlify, unhexlify

app = Flask(__name__)

app.config.from_pyfile('../config.default.py')
app.config.from_pyfile('../config.py')
app.config['SESSION_REDIS'] = redis.from_url(app.config['SESSION_REDIS'])
app.secret_key = app.config['SECRET_KEY']

server_session = Session(app)

hive_keychain_auth = Blueprint(
    'hive_keychain_auth',
    __name__,
    static_folder='static',
    static_url_path='/hive_keychain_auth',
    template_folder='templates',
)

@hive_keychain_auth.route("/login")
@hive_keychain_auth.route("/login/<path:redirect_url>")
def login(redirect_url = ''):
    if 'username' in session.keys():
        return redirect('/'+redirect_url)
    return render_template('login.html',redirect_url=redirect_url,notabs=True)

@hive_keychain_auth.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('hive_keychain_auth.login'))

@hive_keychain_auth.route('/verify-login', methods=['POST'])
def verify_login():
    data = request.json
    datakey = data.get('publicKey')
    pubkey = PublicKey(datakey)
    signed_message = data.get('result')
    data = data.get('data')
    username = data['username']
    message = data['message']
    
    try:        
        msgkey = verify_message(message, unhexlify(signed_message))
        pk = PublicKey(hexlify(msgkey).decode("ascii"))
        if str(pk) == str(pubkey):
            acc = Account(username, lazy=True)
            match = False
            for key in acc["posting"]["key_auths"]:
                match = match or datakey in key
            if match:
                session['username'] = username
                return jsonify({"status": "success", "message": f"Verified login for {username}."})
            return jsonify({"status": "error", "message": "Verification failed."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
