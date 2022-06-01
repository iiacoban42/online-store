import os
import sys
import atexit
import time

from models import *
from scripts import *

import collections

import psycopg2

class _DatabaseConnection:
    def __init__(self):
        self.db = psycopg2.connect(host=os.environ['POSTGRES_HOST'],
                                   port=int(os.environ['POSTGRES_PORT']),
                                   user=os.environ['POSTGRES_USER'],
                                   password=os.environ['POSTGRES_PASSWORD'],
                                   database=int(os.environ['POSTGRES_DB']))
        self._create_db()
        atexit.register(self._close_db_connection)

    def _close_db_connection(self):
            self.db.close()

    def cursor(self):
        return self.db.cursor()

    def commit(self):
        self.db.commit()

    def _create_db(self):
        self.cursor().execute(create_table_script)
        self.commit()

    def create_item(self, item_price):
        cursor = self.cursor()
        cursor.execute(insert_item_script, (item_price, ))
        new_item_id = cursor.fetchone()[0]
        self.commit()
        return new_item_id


    def find_item(self, item_id):
        cursor = self.cursor()
        cursor.execute(find_item_script, (item_id, ))
        item = cursor.fetchone()
        self.commit()
        return Item(item[0], item[1], item[2])


    def add_stock(self, item_id, amount):
        cursor = self.cursor()
        cursor.execute(add_item_stock_script, (amount, item_id))
        self.commit()


    def remove_stock(self, item_id, amount):
        cursor = self.cursor()
        cursor.execute(remove_item_stock_script, (amount, item_id))
        self.commit()

    def remove_stock_request(self, xid, item_id, amount):
        self.db.tpc_begin(xid)
        cursor = self.cursor()
        cursor.execute(remove_item_stock_script, (amount, item_id))
        # self.commit()
        self.db.tpc_prepare()
        self.db.reset()


    def calculate_cost(self, xid, item_ids):
        self.db.tpc_begin(xid)
        cursor = self.cursor()

        counts = dict(collections.Counter(item_ids))

        cursor.execute(calculate_cost_script, (tuple(i for i in item_ids),))
        result = cursor.fetchall()

        cost = 0
        for t in result:
            cost += counts[t[0]] * t[1]

        self.db.tpc_prepare()
        self.db.reset()
        return cost

    def commit_transaction(self, xid):
        self.db.tpc_commit(xid)

    def rollback_transaction(self, xid):
        self.db.tpc_rollback(xid)


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")