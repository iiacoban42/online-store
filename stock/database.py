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
        try:
            cursor = self.cursor()
            cursor.execute(insert_item_script, (item_price,))
            new_item_id = cursor.fetchone()[0]
            self.commit()
        except Exception as e:
            raise e
        finally:
            self.db.reset()
        return new_item_id

    def find_item(self, item_id):
        cursor = self.cursor()
        cursor.execute(find_item_script, (item_id,))
        item = cursor.fetchone()
        self.commit()
        return item

    def add_stock(self, item_id, amount):
        cursor = self.cursor()
        cursor.execute(add_item_stock_script, (amount, item_id))
        modified_item = cursor.fetchone()
        self.commit()
        return modified_item

    def remove_stock(self, item_id, amount):
        try:
            cursor = self.cursor()
            cursor.execute(remove_item_stock_script, (amount, item_id))
            modified_item = cursor.fetchone()
            self.commit()
        except Exception as e:
            raise e
        finally:
            self.db.reset()
        return modified_item

    def remove_stock_request(self, xid, counts):
        try:
            self.db.tpc_begin(xid)
            cursor = self.cursor()
            for _id, count in counts.items():
                cursor.execute(remove_item_stock_script, (count, _id))
            self.db.tpc_prepare()
        except Exception as e:
            raise e
        finally:
            self.db.reset()

    def calculate_cost(self, item_ids):

        cursor = self.cursor()

        counts = dict(collections.Counter(item_ids))

        cursor.execute(calculate_cost_script, (tuple(i for i in item_ids),))
        result = cursor.fetchall()

        available_stock = []
        cost = 0
        for t in result:
            available_stock.append(tuple([t[0], t[2]]))
            cost += counts[t[0]] * t[1]

        return cost, available_stock

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
