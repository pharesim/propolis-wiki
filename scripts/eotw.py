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
import datetime
import json
import requests

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

today = datetime.date.today()
tots = today - datetime.timedelta(days=1)
fromts = today - datetime.timedelta(days=8)
pprint('from '+fromts.strftime('%Y-%m-%d %H:%M')+' to '+tots.strftime('%Y-%m-%d %H:%M'))
cur.execute('SELECT trx_id, timestamp, permlink, author FROM comments WHERE timestamp > %s AND timestamp < %s ORDER BY timestamp ASC;',(fromts,tots,))
edits = cur.fetchall()
collection = {
    'by_author':{},
    'by_post':{}
}
for edit in edits:
    post = hive.get_transaction(edit[0])
    body = post['operations'][0]['value']['body']
    if edit[3] in collection['by_author']:
        if edit[2] in collection['by_author'][edit[3]]:
            collection['by_author'][edit[3]][edit[2]]['count'] = collection['by_author'][edit[3]][edit[2]]['count']+1
            collection['by_author'][edit[3]][edit[2]]['last'] = edit[0]
            collection['by_author'][edit[3]][edit[2]]['edits'].append(len(body))
        else:
            collection['by_author'][edit[3]][edit[2]] = {
                'first':edit[0],
                'count':1,
                'edits':[len(body)]
            }
    else:
        collection['by_author'][edit[3]] = {
            edit[2]:{
                'first':edit[0],
                'count':1,
                'edits':[len(body)]
            }
        }
    if edit[2] in collection['by_post']:
        if edit[3] in collection['by_post'][edit[2]]:
            collection['by_post'][edit[2]][edit[3]]['count'] = collection['by_post'][edit[2]][edit[3]]['count']+1
            collection['by_post'][edit[2]][edit[3]]['last'] = edit[0]
            collection['by_post'][edit[2]][edit[3]]['edits'].append(len(body))
        else:
            collection['by_post'][edit[2]][edit[3]] = {
                'first':edit[0],
                'count':1,
                'edits':[len(body)]
            }
    else:
        collection['by_post'][edit[2]] = {
            edit[3]:{
                'first':edit[0],
                'count':1,
                'edits':[len(body)]
            }
        }
pprint(collection)
