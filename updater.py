from beem import Hive
from beem.account import Account
from beem.comment import Comment
from beem.blockchain import Blockchain
from beembase.signedtransactions import Signed_Transaction
from beemgraphenebase.base58 import Base58
from beem.wallet import Wallet

from pprint import pprint
import time
import json

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

        if(exists == False and op['type'] == 'comment' and op['author'] == conf['WIKI_USER'] and op['parent_permlink'] == 'wiki' and op['block'] != startblock):
            pprint('Processing transaction '+op['trx_id'])
            metadata = json.loads(op['json_metadata'])
            
            signer = ''
            transaction = Signed_Transaction(hive.get_transaction(op['trx_id']))
            for key in transaction.verify(chain='HIVE2'):
                owner = w.getAccountFromPublicKey('STM'+str(Base58(data=key)))
                if(owner != None):
                    signer = owner
            try:
                if(signer == metadata['appdata']['user']):
                    signer = True
                else:
                    signer = False
            except:
                signer = False
            if(signer == False):
                pprint("User in metadata isn't signer. Remove signer's access and print in log.")  
            
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
                if(tag != 'wiki'):
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