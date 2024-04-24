import redis
from flask import Flask, render_template, redirect, session
from flask_session import Session

from hive_keychain_auth.auth import hive_keychain_auth

from beem.account import Account
from beem.comment import Comment

app = Flask(__name__)

app.config.from_pyfile('config.default.py')
app.config.from_pyfile('config.py')

app.config['SESSION_REDIS'] = redis.from_url(app.config['SESSION_REDIS'])
app.secret_key = app.config['SECRET_KEY']
server_session = Session(app)

app.register_blueprint(hive_keychain_auth)

def hive_broadcast(op):
    from beem.transactionbuilder import TransactionBuilder
    tx = TransactionBuilder()
    tx.appendOps(op)
    tx.appendWif(app.config['ACTIVE_KEY'])
    tx.sign()
    return tx.broadcast()

def hive_account_update(account_data):
    from beembase import operations
    op = operations.Account_update(**account_data)
    return hive_broadcast(op)

@app.context_processor
def inject_session_data():
    return dict(session=session)

@app.before_request
def before_request():
    if 'username' not in session.keys():
        session.pop('userlevel',None)
    if 'username' in session.keys() and 'userlevel' not in session.keys():
        userlevel = 0
        account = Account(app.config['WIKI_USER'])
        for key in account["posting"]["account_auths"]:
            if key[0] == session['username']:
                userlevel = key[1]
        session['userlevel'] = userlevel

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/wiki')
def redirect_home():
    return redirect('/')

@app.route('/article')
def article():
    return render_template('article.html')

@app.route('/create')
@app.route('/create/<article_title>')
def create(article_title = ''):
    if(article_title[:1].islower()):
        return redirect('/create/'+article_title[:1].upper()+article_title[1:])
    
    if 'username' in session.keys():
        return render_template('edit.html',article_title=article_title,notabs=True)
    else:
        return redirect('/login/create')    
    
@app.route('/edit/<article_title>')
def edit(article_title):
    if(article_title[:1].islower()):
        return redirect('/edit/'+article_title[:1].upper()+article_title[1:])
    
    if 'username' in session.keys():
        try:
            post = Comment(app.config['WIKI_USER']+"/"+article_title[:1].lower()+article_title[1:])
            return render_template('edit.html',post=post,article_title=article_title)
    
        except:
            return redirect('/create/'+article_title)
    else:
        return redirect('/login/edit/'+article_title)

@app.route('/wiki/<hive_post>')
def wiki(hive_post):
    if(hive_post[:1].islower()):
        hive_post = hive_post[:1].upper()+hive_post[1:]
        return redirect('/wiki/'+hive_post)
    
    hive_post = hive_post[:1].lower()+hive_post[1:]
    try:
        post = Comment(app.config['WIKI_USER']+"/"+hive_post)
        if 'last_update' in post:
            last_update = [post['last_update']]
        else:
            last_update = [post['created']]

        if post['json_metadata']['appdata']['user']:
            last_update.append(post['json_metadata']['appdata']['user'])

        return render_template('wiki.html',post=post,last_update=last_update)
    
    except:
        post = {'title': hive_post[:1].upper()+hive_post[1:], 'body': 'Article not found. [Create](/create/'+hive_post+') it now!'}
        return render_template('wiki.html',post=post)
    
@app.route('/source/<hive_post>')
def source(hive_post):
    if(hive_post[:1].islower()):
        hive_post = hive_post[:1].upper()+hive_post[1:]
        return redirect('/source/'+hive_post)
    
    hive_post = hive_post[:1].lower()+hive_post[1:]
    try:
        post = Comment(app.config['WIKI_USER']+"/"+hive_post)
        return render_template('source.html',post=post,article_title=hive_post[:1].upper()+hive_post[1:])
    
    except:
        return redirect('/create/'+hive_post)

@app.route('/setup')
def setup():
    log = '';
    account = Account(app.config['WIKI_USER'])
    if(account["posting"]["account_auths"] == []):
        if(session['username']):
            account["posting"]["account_auths"] = [[session['username'],3]]
            hive_account_update(
                {"account": app.config['WIKI_USER'],
                "posting": account["posting"],
                "memo_key": account["memo_key"],
                "json_metadata": account["json_metadata"]}
            )
            log = log + 'Created admin account '+session['username']+'<br />'
        else:
            log = log + 'No admin set, but not logged in. <a href="/login/setup">Log in</a> and try again<br />'
    else:
        log = log + 'Account has permissions set, skipping.<br />'

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)