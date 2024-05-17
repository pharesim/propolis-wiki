from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.transactionbuilder import TransactionBuilder
from beem.wallet import Wallet
from beembase import operations
from beembase.signedtransactions import Signed_Transaction
from beemgraphenebase.base58 import Base58

from pprint import pprint
import time
import json
import requests

from configparser import ConfigParser
from itertools import chain

import psycopg2

parser = ConfigParser()
with open("./instance/config.py") as lines:
    lines = chain(("[top]",), lines)
    parser.read_file(lines)
conf = parser['top']
for i, v in conf.items():
    conf[i] = v[1:-1]

conn = psycopg2.connect(
    host=conf['DB_HOSTNAME'],
    database=conf['DATABASE'],
    user=conf['DB_USERNAME'],
    password=conf['DB_PASSWORD'])

client = Hive()
acc = Account(conf['WIKI_USER'])
hive = Blockchain()
w = Wallet()

def formatPostLink(permlink):
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

def webhook_send(text):
    url = conf['DISCORD_WEBHOOK']
    data = {}
    data["content"] = text
    data["username"] = conf['WIKI_USER']+" activity"
    return requests.post(url, json=data, headers={"Content-Type": "application/json"})

def send_to_waves(title,metadata,link):
    text = metadata['appdata']['user']+' has edited the Propolis Wiki article '+title+"\n"
    if('reason' in metadata['appdata']):
        text += 'Reason: '+metadata['appdata']['reason']+"\n"
    text += link
    for w in conf['WAVES_ACCOUNTS']:
        wa = Account(w)
        for post in wa.blog_history(limit=1,reblogs=False):
            pprint("Send to "+wa+'/'+post['permlink']+":\n"+text)

# start from block after wiki user account creation
startblock = 0
for op in acc.history(use_block_num=False,start=0,stop=1):
    startblock = op['block']

while 1 == 1:
    cur = conn.cursor()
    for op in acc.history(only_ops=['comment'],start=startblock):
        cur.execute('SELECT trx_id FROM comments WHERE trx_id=%s',(op['trx_id'],))
        try: 
            exists = cur.fetchall()[0]
        except:
            exists = False

        # Only process comments that don't exist yet, were authored by the wiki user in the category wiki
        if(exists == False and op['type'] == 'comment' and op['author'] == conf['WIKI_USER'] and op['parent_permlink'] == 'wiki' and op['block'] != startblock):
            pprint('Processing transaction '+op['trx_id'])

            metadata = json.loads(op['json_metadata'])
            if 'appdata' not in metadata or 'user' not in metadata['appdata']:
                metadata['appdata']['user'] = None

            webhook_text = 'New edit by '+metadata['appdata']['user']+' on article '+op['title']
            if 'reason' in metadata['appdata']:
                webhook_text += ' ('+metadata['appdata']['reason']+')'
            rev_link = 'https://propol.is/history/'+formatPostLink(op['permlink'])+'/revision/'+op['trx_id']
            webhook_text += ' '+rev_link
            webhook_send(webhook_text)
            #send_to_waves(op['title'],metadata,rev_link)

            transaction = Signed_Transaction(hive.get_transaction(op['trx_id']))
            signer = ''
            for key in transaction.verify(chain='HIVE2'):
                owner = w.getAccountFromPublicKey('STM'+str(Base58(data=key)))
                if(owner != None):
                    signer = owner
            try:
                if(signer == metadata['appdata']['user']):
                    s = True
                else:
                    s = False
            except:
                s = False
            if(s == False):
                pprint("User in metadata isn't signer. Removing signer's access.")
                webhook_send("User in metadata didn't sign the transaction. Removing authorization for "+signer)
                account = Account(conf['WIKI_USER'])
                for i, auth in enumerate(account["posting"]["account_auths"]):
                    if(auth[0] == signer):
                        account['posting']['account_auths'].pop(i)
                        op = operations.Account_update(**{"account": conf['WIKI_USER'],
                            "posting": account["posting"],
                            "memo_key": account["memo_key"],
                            "json_metadata": account["json_metadata"]})
                        tx = TransactionBuilder()
                        tx.appendOps(op)
                        tx.appendWif(conf['ACTIVE_KEY'])
                        tx.sign()
                        tx.broadcast()
                        break
                metadata['appdata']['user'] = None
            
            time.sleep(15)
            post = Comment(conf['WIKI_USER']+"/"+op['permlink'])           
            tags = metadata['tags']
            abstract = ''
            body = post['body']
            split = post['body'].split("\n## ",1)
            if(len(split) > 1):
                abstract = split[0]
                body = split[1]
            cur.execute('INSERT INTO posts (permlink, title, tsvector)'
                " VALUES (%s, %s, setweight(to_tsvector(coalesce(%s,'')), 'A') || setweight(to_tsvector(coalesce(%s,'')), 'B') || setweight(to_tsvector(coalesce(%s,'')), 'C') || setweight(to_tsvector(coalesce(%s,'')), 'D'))"
                ' ON CONFLICT(permlink) DO UPDATE SET tsvector = EXCLUDED.tsvector',
                (op['permlink'], op['title'], op['title'], ' '.join(tags), abstract, body))
            cur.execute('INSERT INTO comments (trx_id, permlink, timestamp, author)'
                ' VALUES (%s, %s, %s, %s)'
                ' ON CONFLICT(trx_id) DO NOTHING',
                (op['trx_id'],op['permlink'],op['timestamp'],metadata['appdata']['user']))
            for tag in tags:
                if(tag != 'wiki' and tag != ''):
                    cur.execute('INSERT INTO categories (category)'
                        ' VALUES (%s)'
                        ' ON CONFLICT(category) DO NOTHING',
                        (tag,))
                    cur.execute('DELETE FROM categories_posts WHERE permlink=%s AND category=%s',
                                (op['permlink'],tag))
                    cur.execute('INSERT INTO categories_posts (permlink, category)'
                        ' VALUES (%s,%s)',
                        (op['permlink'],tag))
        startblock = op['block']

    conn.commit()
    cur.close()
    time.sleep(3)

conn.close()