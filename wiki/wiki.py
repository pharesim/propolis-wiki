from flask import (
    Blueprint, Response, flash, redirect, render_template, url_for, request, session, current_app
)
from werkzeug.exceptions import abort

import time
import json

import psycopg2

from diff_match_patch import diff_match_patch

from beem.account import Account
from beem.comment import Comment
from beem.blockchain import Blockchain

from markupsafe import Markup
import bleach

bp = Blueprint('wiki', __name__)

def get_db_connection():
    conn = psycopg2.connect(host=current_app.config['DB_HOSTNAME'],
                            database=current_app.config['DATABASE'],
                            user=current_app.config['DB_USERNAME'],
                            password=current_app.config['DB_PASSWORD'])
    return conn

def db_get_all(query,data = ()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query,data)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def db_count(query,data = ()):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query,data)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result

def xssEscape(string):
    string = bleach.clean(
        string,
        tags = {'a','br','b','center','div','h4','i','img','li','p','ref','span','sub','sup','table','tbody','td','thead','th','tr','ul'},
        attributes = {
            'a': ['class', 'href', 'id', 'title'],
            'div': ['class'],
            'img': ['src'],
            'p': ['class','id'],
            'span': ['class','id','title'],
            'td': ['colspan'],
            'th': ['colspan'],
        }
    )
    return string

def hive_broadcast(op):
    from beem.transactionbuilder import TransactionBuilder
    tx = TransactionBuilder()
    tx.appendOps(op)
    tx.appendWif(current_app.config['ACTIVE_KEY'])
    tx.sign()
    return tx.broadcast()

def hive_account_update(account_data):
    from beembase import operations
    op = operations.Account_update(**{"account": current_app.config['WIKI_USER'],
            "posting": account_data["posting"],
            "memo_key": account_data["memo_key"],
            "json_metadata": account_data["json_metadata"]})
    return hive_broadcast(op)

def formatPostLink(permlink):
    permlink = permlink.replace('(','').replace(')','').replace(',','')
    split = permlink.split("-")
    if(len(split) > 1):
        permlink = ''
        for i, val in enumerate(split):
            permlink += formatPostLinkSegment(val)
            if(i+1 < len(split)):
                permlink += '-'
    else:
        permlink = formatPostLinkSegment(permlink)
    return permlink

def formatPostLinkSegment(segment):
    split = segment.split(':')
    if(len(split) > 1):
        segment = ''
        for i, s in enumerate(split):
            segment += formatPostLinkSegment(s)
            if(i+1 < len(split)):
                segment += ':'
        return segment
    keeplow = ['Disambiguation','disambiguation']
    if(segment not in keeplow):
        return segment.capitalize()
    if(segment in keeplow):
        return segment.lower()
    return segment

def unformatPostLink(hive_post):
    split = hive_post.split("-")
    hive_post = ''
    for i, val in enumerate(split):
        hive_post += val[:1].lower()+val[1:]
        if(i+1 < len(split)):
            hive_post += '-'
    return hive_post

def restoreSource(body):
    return restoreReferences(wikifyInternalLinks(body))

def restoreReferences(body):
    return body.replace('<ref>|Reference: ','<ref>')

def wikifyInternalLinks(body):
    return body.replace('](/@'+current_app.config['WIKI_USER']+'/','](/wiki/').replace('<a href="/@'+current_app.config['WIKI_USER']+'/','<a href="/wiki/')

def extractCodeBlocks(body):
    new_body = ''
    codeblocks = []
    parts = body.split("```")
    in_code = 0
    for val in parts:
        if in_code == 1:
            new_body += "```"
            codeblocks.append(val)
            in_code = 0
            new_body += "```"
        else:
            new_body += val
            in_code = 1
    return new_body, codeblocks

def restoreCodeBlocks(body,codeblocks):
    new_body = ''
    in_code = 0
    n = 0
    parts = body.split("```")
    for val in parts:
        if in_code == 1:
            new_body += "```"
            new_body += codeblocks[n]
            n = n+1
            in_code = 0
            new_body += "```"
        else:
            new_body += val
            in_code = 1
    return new_body

def wikifyReferences(body):
    references = {}
    refsplit = body.replace('<ref name=multiple>','<ref>').split("<ref>")
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
    return new_body

def wikifyHeaders(body):
    headers = body.split("\n## ")
    new_body = body
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
                            new_body += h
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
        if(z[0][0:5] != '<span'):
            z[0] = '<span id="'+toHtmlId(z[0])+'">'+z[0]+'</span>'
        new_body = headers[0]+contents+"\n\n"+'## '+z[0]+"\n"+z[1]
    return new_body

def wikifyBody(body):
    new_body, codeblocks = extractCodeBlocks(restoreSource(body))

    new_body = wikifyReferences(new_body)

    related, new_body = getRelated(new_body)
    if len(related) > 0:
        new_body += "\n## Related Articles\n"
        for val in related:
            new_body += '<span title="'+val[2]+'"'
            if(val[1] < 1):
                new_body += ' class="article404"'
            new_body += '>'+val[0]+"</span>\n"
    
    new_body = wikifyHeaders(new_body)
    return restoreCodeBlocks(new_body,codeblocks)

def getRelated(new_body):
    related = []
    splitters = ["](/wiki/",")","["]
    relsplit = new_body.split(splitters[0])
    if(len(relsplit) > 1):
        new_body = ''
        for i, val in enumerate(relsplit):
            relrest = val.split(splitters[1])
            if(i > 0):
                link = relrest[0]
                rel = splitters[2]+title+splitters[0]+formatPostLink(link)+splitters[1]
                exists = db_count('SELECT count(permlink) FROM posts WHERE permlink=%s',(unformatPostLink(link),))
                tuple = (rel,exists,title)      
                if ':' not in link and tuple not in related:                         
                    related.append(tuple)
                new_body += splitters[0]
            relbef = val.split(splitters[2])
            split = relbef[0].split(splitters[1],1)
            link = split[0]
            if(len(split) == 1):
                new_body += relbef[0]
            else:
                new_body += link+splitters[1]+split[1]
            if(len(relbef) > 1):
                for j, v in enumerate(relbef):
                    if j > 0:
                        title = v
                        new_body += splitters[2]+title
    if len(related) > 0:
        for val in related:
            string = '<span title="'+val[2]+'" class="'
            if(val[1] < 1):
                string += 'article404'
            else:
                string += 'articleExists'
            new_body = new_body.replace(val[0],string+'">'+val[0]+'</span>')
    return related, new_body
    
def toHtmlId(string):
    return string.replace(' ','').replace(',','').replace(':','').replace('.','')

def getRevisionBody(permlink,trx_id):
    dmp = diff_match_patch()
    last_edit = db_get_all('SELECT trx_id FROM comments WHERE permlink=%s ORDER BY timestamp DESC LIMIT 1;',(permlink,))[0]
    hive = Blockchain()
    patch = []
    if(last_edit[0] == trx_id):
        body = Comment(current_app.config['WIKI_USER']+'/'+permlink).body
    else:
        timestamp = db_get_all('SELECT timestamp FROM comments WHERE trx_id=%s ORDER BY timestamp DESC LIMIT 1;',(trx_id,))[0][0]
        edits_before = db_get_all('SELECT trx_id FROM comments WHERE permlink=%s and timestamp <= %s ORDER BY timestamp ASC',(permlink,timestamp,))
        body = ''
        for edit in edits_before:
            rev = hive.get_transaction(edit[0])['operations'][0]['value']
            try:
                patch += (dmp.patch_fromText(rev['body']))
            except: 
                body = rev['body']
    if(len(patch) > 0):
        body = dmp.patch_apply(patch,body)[0]
    return restoreSource(body)

def replaceLinebreaks(body):
    return body.replace("\n",'<br>')

@bp.context_processor
def inject_session_data():
    return dict(session=session)

@bp.before_request
def before_request():
    if 'username' not in session.keys():
        session.pop('userlevel',None)
    if 'username' in session.keys():
        userlevel = 0
        account = Account(current_app.config['WIKI_USER'])
        for key in account["posting"]["account_auths"]:
            if key[0] == session['username']:
                userlevel = key[1]
        session['userlevel'] = userlevel

@bp.route('/wiki')
def redirect_home():
    return redirect('/',301)

@bp.route('/pages/<page>')
def pages(page):
    return render_template(page+'.html',notabs=True,pagetitle=page.capitalize())

@bp.route('/create', defaults={'article':''})
@bp.route('/create/<article>')
def create(article):
    article_f = formatPostLink(article)
    if 'username' not in session.keys():
        return redirect(url_for('wiki.hive_keychain_auth.login',redirect_url='create/'+article_f))
    if(session['userlevel'] < 1):
        return redirect('/insufficient_permissions') 
    if(article_f != article):
        return redirect(url_for('wiki.create', article=article_f),301) 
    
    return render_template('edit.html',article_title=article.replace('-',' '),notabs=True,pagetitle='Create article')
    
@bp.route('/insufficient_permissions')
def insufficient_permissions():
    return render_template('insufficient_permissions.html',notabs=True,pagetitle='Insufficient permissions')

@bp.route('/edit/<article>')
def edit(article):
    article_f = formatPostLink(article)
    if 'username' not in session.keys():
        return redirect(url_for('wiki.hive_keychain_auth.login',redirect_url='edit/'+article_f))
    if(session['userlevel'] < 1):
        return redirect('/insufficient_permissions') 
    if(article_f != article):
        return redirect(url_for('wiki.edit', article=article_f),301) 
    permlink = unformatPostLink(article_f)
        
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
        body = Markup(xssEscape(restoreSource(post.body)))
        post.json_metadata['tags'].remove('wiki')
        return render_template('edit.html',post=post,body=body,article_title=post.title,pagetitle='Edit article')
    except:
        return redirect(url_for('wiki.create', article=article_f))
        
@bp.route('/', defaults={'article':''})
@bp.route('/wiki/<article>')
def wiki(article):
    if(article == ''):
        return redirect(url_for('wiki.wiki', article=formatPostLink(current_app.config['START_PAGE'])))
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.wiki', article=article_f),301)  
    permlink = unformatPostLink(article_f)

    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
        last_update = [db_get_all('SELECT timestamp FROM comments WHERE permlink=%s ORDER BY timestamp DESC LIMIT 1',(permlink,))[0][0]]
        if post.json_metadata['appdata']['user']:
            last_update.append(post.json_metadata['appdata']['user'])   
        body = Markup(xssEscape(wikifyBody(post.body)))
        return render_template('wiki.html',post=post,body=body,last_update=last_update)  
    except:
        post = {
            'title': article_f,
            'body': "The community has yet to [write this article](/create/"+article_f+").\n\nThis is where you step in. Care to write what you know from a simple description or even a full, referenced wiki? Content will be community-fed and edited, you will be helping the cause and qualify for a weekly content reward.\n\n[Give it a try!](/create/"+article_f+")"
        }
        return render_template('wiki.html',post=post,body=post['body'])
    
@bp.route('/@<username>/<permlink>')
def reroute(username, permlink):
    if(username == current_app.config['WIKI_USER']):
        return redirect(url_for('wiki.wiki', article=formatPostLink(permlink)),301)
    else:
        return redirect('/',301)

@bp.route('/source/<article>')
def source(article):
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.source', article=article_f),301)   
    permlink = unformatPostLink(article_f)
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
        return render_template('source.html',post=post,body=restoreSource(post.body),pagetitle='View source')   
    except:
        return redirect(url_for('wiki.create', article=article_f))
    
@bp.route('/search/<search>')
def search(search):
    results = db_get_all('SELECT permlink FROM posts WHERE tsvector @@ websearch_to_tsquery(%s);',(search,))
    return render_template('search.html',search=search,results=results)

@bp.route('/activity')
def activity():
    data = db_get_all('SELECT trx_id, timestamp, permlink, author FROM comments ORDER BY timestamp DESC;')
    edits = []
    for i, edit in enumerate(data):
        try:
            before = db_get_all('SELECT trx_id FROM comments WHERE permlink = %s AND timestamp<%s ORDER BY timestamp DESC LIMIT 1;',(edit[2],edit[1],))[0]
            edits.append([edit[0],edit[1],formatPostLink(edit[2]),edit[3],before[0]])
        except:
            edits.append([edit[0],edit[1],formatPostLink(edit[2]),edit[3],''])
    return render_template('activity.html',edits=edits,notabs=True,pagetitle='Activity')

@bp.route('/history/<article>')
def history(article):
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.history', article=article_f),301)   
    permlink = unformatPostLink(article_f)
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
    except:
        return redirect(url_for('wiki.create', article=article_f))
        
    edits = db_get_all('SELECT trx_id, timestamp FROM comments WHERE permlink=%s ORDER BY timestamp DESC',(permlink,))
    return render_template('history.html',post=post,permlink=article_f,edits=edits,pagetitle='Article history')

@bp.route('/revision/<trx_id>')
def revision_raw(trx_id):
    return redirect(url_for('wiki.revision', article=formatPostLink(db_get_all('SELECT permlink FROM comments WHERE trx_id=%s LIMIT 1;',(trx_id,))[0][0]), trx_id=trx_id),301)

@bp.route('/history/<article>/revision/<trx_id>')
def revision(article, trx_id):
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.revision', article=article_f, trx_id=trx_id),301)
    
    permlink = unformatPostLink(article_f)
    hive = Blockchain()
    post = hive.get_transaction(trx_id)
    post = post['operations'][0]['value']
    post['json_metadata'] = json.loads(post['json_metadata'])

    body = Markup(xssEscape(wikifyBody(getRevisionBody(permlink,trx_id))))
    last_update = [db_get_all('SELECT timestamp FROM comments WHERE trx_id=%s LIMIT 1;',(trx_id,))[0][0],post['json_metadata']['appdata']['user']]
    latest = db_get_all('SELECT trx_id, timestamp, author FROM comments WHERE permlink=%s ORDER BY timestamp DESC LIMIT 1',(permlink,))[0]
    latest_update = [latest[1],latest[2]]
    latest_revision = latest[0]
    if(latest_revision == trx_id):
        return redirect(url_for('wiki.wiki', article=article))
    try:
        older_revision = db_get_all('SELECT trx_id FROM comments WHERE permlink=%s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1',(permlink,last_update[0]))[0][0]
    except:
        older_revision = ''
    newer_revision = db_get_all('SELECT trx_id FROM comments WHERE permlink=%s AND timestamp > %s ORDER BY timestamp ASC LIMIT 1',(permlink,last_update[0]))[0][0]
    return render_template('wiki.html',pagetitle='Revision',post=post,body=body,last_update=last_update,revision=trx_id,permlink=article_f,latest_update=latest_update,latest_revision=latest_revision,older_revision=older_revision,newer_revision=newer_revision)

@bp.route('/history/<article>/compare/<revision_1>/<revision_2>')
def compare(article, revision_1, revision_2):
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.compare', article=article_f, revision_1=revision_1, revision_2=revision_2),301)  
    permlink = unformatPostLink(article)
    body_1 = Markup(xssEscape(replaceLinebreaks(getRevisionBody(permlink,revision_1).replace("'","|0x27|").replace('<ref>','[* ').replace('</ref>',']'))))
    body_2 = Markup(xssEscape(replaceLinebreaks(getRevisionBody(permlink,revision_2).replace("'","|0x27|").replace('<ref>','[* ').replace('</ref>',']'))))
    data_1 = db_get_all('SELECT timestamp, author, trx_id FROM comments WHERE trx_id=%s LIMIT 1',(revision_1,))[0]
    data_2 = db_get_all('SELECT timestamp, author, trx_id FROM comments WHERE trx_id=%s LIMIT 1',(revision_2,))[0]
    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
    except:
        return redirect(url_for('wiki.create', article=article_f))
    return render_template('compare.html',pagetitle='Compare revisions',post=post,permlink=formatPostLink(permlink),body_1=body_1,body_2=body_2,data_1=data_1,data_2=data_2)
    
@bp.route('/talk/<article>')
def talk(article):
    article_f = formatPostLink(article)
    if(article_f != article):
        return redirect(url_for('wiki.talk', article=article_f),301)
    permlink = unformatPostLink(article)

    try:
        post = Comment(current_app.config['WIKI_USER']+"/"+permlink)
        data = Comment(current_app.config['WIKI_USER']+'/'+permlink).get_all_replies()
        replies = []
        for d in data:
            replies.append({
                'body': Markup(xssEscape(d.body)),
                'short': Markup(xssEscape(d.body[0:55]+'...'))
            })
        return render_template('talk.html',permlink=permlink,post=post,data=data,replies=replies,pagetitle='Talk')
    except:
        return redirect(url_for('wiki.create', article=article_f))


@bp.route('/wiki/Categories:Overview')
def categories():
    categories = db_get_all('SELECT category FROM categories ORDER BY category;')
    for i, category in enumerate(categories):
        categories[i] = (categories[i][0],db_count('SELECT count(category) FROM categories_posts WHERE category=%s;',(category[0],)))
    return render_template('categories.html', categories=categories,notabs=True,pagetitle='Categories')

@bp.route('/wiki/Category:<category>')
def category(category):
    data = db_get_all('SELECT permlink FROM categories_posts WHERE category=%s;',(category.lower(),))
    posts = []
    for i, post in enumerate(data):
        posts.append({
            'article': formatPostLink(post[0]),
            'title': Comment(current_app.config['WIKI_USER']+"/"+post[0]).title
        })
    return render_template('category.html', category=category,posts=posts,notabs=True,pagetitle=category.capitalize())

@bp.route('/random')
def random_article():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT permlink FROM posts;')
    permlinks = cur.fetchall()
    cur.close()
    conn.close()
    import random
    rand = random.randint(0, len(permlinks)-1)
    return redirect(url_for('wiki.wiki', article=formatPostLink(permlinks[rand][0])))

@bp.route('/contributions')
def contributions():
    if('username' not in session):
        return redirect(url_for('wiki.hive_keychain_auth.login', redirect_url='contributions'))
    data = db_get_all('SELECT trx_id, timestamp, permlink FROM comments WHERE author=%s ORDER BY timestamp DESC;',(session['username'],))
    edits = []
    for i, edit in enumerate(data):
        edits.append([edit[0],edit[1],formatPostLink(edit[2])])
    return render_template('contributions.html',edits=edits,notabs=True,pagetitle='My contributions')

@bp.route('/admin')
def admin():
    return redirect('/')

@bp.route('/admin/users')
def admin_users():
    if(session['userlevel'] < 2):
        return redirect('/')
    
    account = Account(current_app.config['WIKI_USER'])
    return render_template('admin/users.html',notabs=True,auths=account["posting"]["account_auths"],pagetitle='User management')

@bp.route('/admin/user/add/<username>/<int:userlevel>')
def admin_user_add(username, userlevel):
    if(session['userlevel'] < 3 and session['userlevel'] <= userlevel):
        flash('You lack the required privileges')
        return redirect('/admin/users')
    
    wiki_user = Account(current_app.config['WIKI_USER'])

    for auth in wiki_user["posting"]["account_auths"]:
        if(auth[0] == username):
            flash('User already registered')
            return redirect('/admin/users')
        
    new_auth = [[username,userlevel]]
    wiki_user["posting"]["account_auths"].extend(new_auth)
    try:
        hive_account_update(wiki_user)
        time.sleep(5)
        flash('User successfully created')
    except:
        flash('User creation failed')

    return redirect('/admin/users')

@bp.route('/admin/user/change/<username>/<int:userlevel>')
def admin_user_change(username, userlevel):
    if(session['userlevel'] < 3 and session['userlevel'] <= userlevel):
        flash('You lack the required privileges')
        return redirect('/admin/users')
    
    wiki_user = Account(current_app.config['WIKI_USER'])

    for i, auth in enumerate(wiki_user["posting"]["account_auths"]):
        if(auth[0] == username):
            wiki_user["posting"]["account_auths"][i][1] = userlevel
            try:
                hive_account_update(wiki_user)
                time.sleep(5)
                flash('Userlevel successfully altered')
            except:
                flash('Updating userlevel failed')

    return redirect('/admin/users')

@bp.route('/admin/user/delete/<username>')
def admin_user_delete(username):
    if(session['userlevel'] < 2):
        flash('You lack the required privileges')
        return redirect('/admin/users')
    
    wiki_user = Account(current_app.config['WIKI_USER'])

    for i, auth in enumerate(wiki_user["posting"]["account_auths"]):
        if(auth[0] == username):
            if(session['userlevel'] < 3 and session['userlevel'] <= auth[1]):
                flash('Your userlevel is too low to do this.')
                return redirect('/admin/users')

            wiki_user["posting"]["account_auths"].pop(i)
            try:
                hive_account_update(wiki_user)
                time.sleep(5)
                flash('User successfully deleted')
            except:
                flash('Deleting user failed')

    return redirect('/admin/users')

@bp.route('/setup')
def setup():
    account = Account(current_app.config['WIKI_USER'])
    if(account["posting"]["account_auths"] == []):
        if(session['username']):
            account["posting"]["account_auths"] = [[session['username'],3]]
            hive_account_update(account)
            flash('Created admin account '+session['username'])
        else:
            flash('No admin set, but not logged in. <a href="/login/setup">Log in</a> and try again')
    else:
        flash('Account has permissions set, skipping')

    return redirect('/')

@bp.route('/robots.txt')
def robots_txt():
    text = "# advertising-related bots:\n"
    text += "User-agent: Mediapartners-Google*\n"
    text += "Disallow: /\n"
    text += "\n"
    text += "User-agent: *\n"
    text += "Allow: /\n"
    text += "Allow: /wiki/"
    text += "\n"
    text += "Sitemap: "+request.url_root+"sitemap.xml"
    return Response(text, mimetype='text/text')

@bp.route('/sitemap.xml')
def sitemap_xml():
    wiki_pages = db_get_all('SELECT permlink FROM posts')
    xml = '<?xml version="1.0" encoding="UTF-8"?>'+"\n"
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"\n"
    for page in wiki_pages:
        last_edit = db_get_all('SELECT timestamp FROM comments WHERE permlink=%s ORDER BY timestamp DESC LIMIT 1',(page[0],))[0][0]
        xml += "    <url>\n"
        xml += "        <loc>"+request.url_root+"wiki/"+formatPostLink(page[0])+"</loc>"
        xml += "        <lastmod>"+last_edit.strftime("%Y-%m-%d")+"</lastmod>"
        xml += "    </url>"
    xml += "</urlset>"
    return Response(xml, mimetype='text/xml')

if __name__ == '__main__':
    bp.run(debug=True)