from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
from werkzeug.exceptions import abort


from beem.account import Account
from beem.comment import Comment

from markupsafe import Markup

bp = Blueprint('wiki', __name__)

def hive_broadcast(op):
    from beem.transactionbuilder import TransactionBuilder
    tx = TransactionBuilder()
    tx.appendOps(op)
    tx.appendWif(current_app.config['ACTIVE_KEY'])
    tx.sign()
    return tx.broadcast()

def hive_account_update(account_data):
    from beembase import operations
    op = operations.Account_update(**account_data)
    return hive_broadcast(op)

@bp.context_processor
def inject_session_data():
    return dict(session=session)

@bp.before_request
def before_request():
    if 'username' not in session.keys():
        session.pop('userlevel',None)
    if 'username' in session.keys() and 'userlevel' not in session.keys():
        userlevel = 0
        account = Account(current_app.config['WIKI_USER'])
        for key in account["posting"]["account_auths"]:
            if key[0] == session['username']:
                userlevel = key[1]
        session['userlevel'] = userlevel

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/wiki')
def redirect_home():
    return redirect('/')

@bp.route('/article')
def article():
    return render_template('article.html')

@bp.route('/create')
@bp.route('/create/<article_title>')
def create(article_title = ''):
    if(article_title[:1].islower()):
        return redirect('/create/'+article_title[:1].upper()+article_title[1:])
    
    if 'username' in session.keys():
        return render_template('edit.html',article_title=article_title,notabs=True)
    else:
        return redirect('/login/create')    
    
@bp.route('/edit/<article_title>')
def edit(article_title):
    if(article_title[:1].islower()):
        return redirect('/edit/'+article_title[:1].upper()+article_title[1:])
    
    if 'username' in session.keys():
        try:
            post = Comment(current_app.config['WIKI_USER']+"/"+article_title[:1].lower()+article_title[1:])
            body = Markup(post.body);
            return render_template('edit.html',post=post,body=body,article_title=article_title)
    
        except:
            return redirect('/create/'+article_title)
    else:
        return redirect('/login/edit/'+article_title)

@bp.route('/wiki/<hive_post>')
def wiki(hive_post):
    if(hive_post[:1].islower()):
        hive_post = hive_post[:1].upper()+hive_post[1:]
        return redirect('/wiki/'+hive_post)
    
    hive_post = hive_post[:1].lower()+hive_post[1:]
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+hive_post)
        if 'last_update' in post:
            last_update = [post['last_update']]
        else:
            last_update = [post['created']]

        if post['json_metadata']['appdata']['user']:
            last_update.append(post['json_metadata']['appdata']['user'])

        body = Markup(wikifyBody(post.body));
        return render_template('wiki.html',post=post,body=body,last_update=last_update)
    
    except:
        post = {'title': hive_post[:1].upper()+hive_post[1:], 'body': 'Article not found. [Create](/create/'+hive_post+') it now!'}
        return render_template('wiki.html',post=post)
    
def wikifyBody(oldBody):
    references = {}
    refsplit = oldBody.split("<ref>")
    new_body = refsplit[0]
    for i, val in enumerate(refsplit):
        if(i > 0):
            refrest = val.split("</ref>")
            if refrest[0] not in references.keys():
                references[refrest[0]] = 1
                num = len(references)
            else:
                references[refrest[0]] = references[refrest[0]]+1
                num = list(references).index(refrest[0])+1
            new_body += '<sup><a href="#reference_'+str(num)+'" id="cite_ref'+str(num)+'_'+str(references[refrest[0]])+'">['+str(num)+"]</a></sup>"
            new_body += refrest[1]

    if len(references) > 0:
        new_body += "\n## References\n"
        i = 0
        for val, times in references.items():
            new_body += str(i+1)+'. ';
            j = 0
            while(j < times):
                j = j+1
                new_body += '<a class="toref" href="#cite_ref'+str(i+1)+'_'+str(j)+'">↑</a> ';
            new_body += '<span id="reference_'+str(i+1)+'">'+val+"</span>\n"
            i = i+1

    related = []
    relsplit = new_body.split("](/wiki/")
    if(len(relsplit) > 1):
        for i, val in enumerate(relsplit):
            if(i > 0):
                relrest = val.split(")")
                link = relrest[0]
                rel = '['+title+'](/wiki/'+link+')'
                if rel not in related:
                    related.append(rel)
            relrest = val.split("[")
            title = relrest[-1]    

    if len(related) > 0:
        new_body += "\n## Related Articles\n"
        for val in related:
            new_body += val+"\n"

    headers = new_body.split("\n## ")
    if(len(headers) > 1):
        new_body = ''
        contents = '<br><div class="contentsPanel"><div class="contentsHeader">Contents</div><ul>'
        for i, val in enumerate(headers):
            if(i > 0):
                heading = val.split("\n")[0]
                contents += '<li><span>'+str(i)+'</span> <a href="#'+toHtmlId(heading)+'">'+heading+'</a>'
                h3s = val.split("\n### ")
                if(len(h3s) > 1):
                    contents += '<ul>'
                    for j, h in enumerate(h3s):
                        if j == 0:
                            new_body = h
                        else:
                            z = h.split("\n",1)
                            new_body += '<span id="'+toHtmlId(z[0])+'">'+z[0]+"</span>\n"+z[1]
                        if(j < len(h3s)-1):
                            new_body += "\n### "
                        if(j > 0):
                            heading = h.split("\n")[0]
                            contents += '<li><span>'+str(i)+'.'+str(j)+'</span> <a href="#'+toHtmlId(heading)+'">'+heading+'</a></li>'
                    contents += '</ul>'
                else:
                    z = val.split("\n",1)
                    new_body += '<span id="'+toHtmlId(z[0])+'">'+z[0]+"</span>\n"+z[1]
                if(i < len(headers)-1):
                    new_body += "\n## "
                contents += '</li>'
        contents += '</ul></div>'
        z = new_body.split("\n",1)
        new_body = headers[0]+contents+"\n\n"+'## '+'<span id="'+toHtmlId(z[0])+'">'+z[0]+"</span>\n"+z[1]
    return new_body
    
def toHtmlId(string):
    return string.replace(' ','').replace(',','').replace(':','').replace('.','')

@bp.route('/source/<hive_post>')
def source(hive_post):
    if(hive_post[:1].islower()):
        hive_post = hive_post[:1].upper()+hive_post[1:]
        return redirect('/source/'+hive_post)
    
    hive_post = hive_post[:1].lower()+hive_post[1:]
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+hive_post)
        return render_template('source.html',post=post,body=post.body,article_title=hive_post[:1].upper()+hive_post[1:])
    
    except:
        return redirect('/create/'+hive_post)

@bp.route('/setup')
def setup():
    log = '';
    account = Account(current_app.config['WIKI_USER'])
    if(account["posting"]["account_auths"] == []):
        if(session['username']):
            account["posting"]["account_auths"] = [[session['username'],3]]
            hive_account_update(
                {"account": current_app.config['WIKI_USER'],
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
    bp.run(debug=True)