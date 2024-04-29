from beem.account import Account
from beem.comment import Comment
#from beem.blockchain import Blockchain

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

acc = Account(conf['WIKI_USER'])
#hive = Blockchain()
startblock = 0
for op in acc.history(use_block_num=False,start=0,stop=1):
    startblock = op['block']

while 1 == 1:
    cur = conn.cursor()
    for op in acc.history(only_ops=['comment'],start=startblock):
        if(op['type'] == 'comment' and op['author'] == conf['WIKI_USER'] and op['parent_permlink'] == 'wiki' and op['block'] != startblock):
            startblock = op['block']
            post = Comment(conf['WIKI_USER']+"/"+op['permlink'])
            #tx = hive.get_transaction(op['trx_id'])
            metadata = json.loads(op['json_metadata'])
            tags = metadata['tags']
            abstract = ''
            cur.execute('INSERT INTO posts (permlink, title, tsvector)'
                " VALUES (%s, %s, setweight(to_tsvector(coalesce(%s,'')), 'A') || setweight(to_tsvector(coalesce(%s,'')), 'B') || setweight(to_tsvector(coalesce(%s,'')), 'C') || setweight(to_tsvector(coalesce(%s,'')), 'D'))"
                ' ON CONFLICT(permlink) DO UPDATE SET tsvector = EXCLUDED.tsvector',
                (op['permlink'], op['title'], op['title'], ' '.join(tags), abstract, post['body']))
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

    conn.commit()
    cur.close()
    time.sleep(3)
    pprint('sleeping')

conn.close()