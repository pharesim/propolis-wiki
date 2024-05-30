from beem.blockchain import Blockchain

from pprint import pprint
import datetime
from configparser import ConfigParser
from itertools import chain

import psycopg2

parser = ConfigParser()
with open("../instance/config.py") as lines:
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

hive = Blockchain()

cur = conn.cursor()

exclude_users = ['pharesim','nikv','hivetrending']

today = datetime.date.today()
tots = today - datetime.timedelta(days=1)
fromts = today - datetime.timedelta(days=8)
pprint('from '+fromts.strftime('%Y-%m-%d %H:%M')+' to '+tots.strftime('%Y-%m-%d %H:%M'))
cur.execute('SELECT trx_id, timestamp, permlink, author FROM comments WHERE timestamp >= %s AND timestamp <= %s ORDER BY timestamp ASC;',(fromts,tots,))
edits = cur.fetchall()
collection = {}
for edit in edits:
    post = hive.get_transaction(edit[0])
    body = post['operations'][0]['value']['body']
    if edit[2] in collection:
        if edit[3] in collection[edit[2]]:
            collection[edit[2]][edit[3]]['count'] += 1
            collection[edit[2]][edit[3]]['last'] = edit[0]
            collection[edit[2]][edit[3]]['edits'] += len(body)
            collection[edit[2]][edit[3]]['timestamp'] = edit[1].strftime('%Y-%m-%d %H:%M')
        else:
            collection[edit[2]][edit[3]] = {
                'first':edit[0],
                'count':1,
                'edits':len(body),
                'timestamp':edit[1].strftime('%Y-%m-%d %H:%M')
            }
    else:
        collection[edit[2]] = {
            edit[3]:{
                'first':edit[0],
                'count':1,
                'edits':len(body),
                'timestamp':edit[1].strftime('%Y-%m-%d %H:%M')
            }
        }
sorted = []
for article, c in collection.items():
    add = {}
    index = 0
    highest = 0
    for author, d in c.items():
        if d['edits'] > highest:
            if(author not in exclude_users):
                highest = d['edits']
                add['highest'] = highest
                add[article] = c
    for i,s in enumerate(sorted):
        if('highest' in s and highest > s['highest']):
            index = i+1
    sorted.insert(index,add)        
sorted.reverse()
for s in sorted:
    for article, t in s.items():
        if article != 'highest':
            txt = 'Article: '+article
            for author, u in t.items():
                if author not in exclude_users:
                    txt += ' Author: '+author
                    txt += ' '+str(u['edits'])+' characters in '+str(u['count'])+' edits'
            pprint(txt)