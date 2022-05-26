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
        total_stock = cursor.fetchone()[0]
        self.commit()
        return total_stock

    def calculate_cost(self, xid, item_ids):
        self.db.tpc_begin(xid)
        cursor = self.cursor()

        counts = dict(collections.Counter(item_ids))
        result = cursor.fetchall()

        cost = 0
        for tuple in result:
            cost += counts[tuple[0]] * tuple[1]

        self.db.tpc_prepare()
        self.db.reset()
        return cost


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")