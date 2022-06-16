import os
import sys
import atexit
import time
from uhashring import HashRing

from models import *
from scripts import *

import collections

import psycopg2


def connect_to_postgres(db_conf):
    conn = psycopg2.connect(**db_conf)
    return conn

class _DatabaseConnection:
    DATABASE_CLIENTS = {
        "5201": {
            "host": "stock-db-1",
            "port": "5201",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
        "5202": {
            "host": "stock-db-2",
            "port": "5202",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
        "5203": {
            "host": "stock-db-3",
            "port": "5203",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
    }

    hash_ring = HashRing(nodes=["5201", "5202", "5203"])

    def __init__(self):
        self.db = {}
        for node in self.DATABASE_CLIENTS:
            self.db[node] = connect_to_postgres(self.DATABASE_CLIENTS.get(node))
            self._create_db(node)
        atexit.register(self._close_db_connection)

    def _close_db_connection(self):
        for node in self.DATABASE_CLIENTS:
            self.db[node].close()

    def cursor(self, node):
        return self.db[node].cursor()

    def commit(self, node):
        self.db[node].commit()

    def _create_db(self, node):
        self.cursor(node).execute(create_table_script)
        self.commit(node)

    def create_item(self, item_price, item_id, node):
        try:
            cursor = self.cursor(node)
                    cursor.execute(insert_item_script, (item_id, item_price,))
                    new_item_id = cursor.fetchone()[0]
                    self.commit(node)
        except Exception as e:
            raise e
        finally:
            self.db.reset()
        return new_item_id

    def find_item(self, item_id, node):
        cursor = self.cursor(node)
        cursor.execute(find_item_script, (item_id,))
        item = cursor.fetchone()
        self.commit(node)
        return item

    def add_stock(self, item_id, amount, node):
        cursor = self.cursor(node)
        cursor.execute(add_item_stock_script, (amount, item_id))
        modified_item = cursor.fetchone()
        self.commit(node)
        return modified_item



    def remove_stock(self, item_id, amount, node):
        try:
            cursor = self.cursor(node)
            cursor.execute(remove_item_stock_script, (amount, item_id, amount))
            modified_item = cursor.fetchone()
            self.commit(node)
        except Exception as e:
            raise e
        finally:
            self.db.reset()
        return modified_item

    def remove_stock_request(self, xid, counts, node):
        try:
            self.db[node].tpc_begin(xid)
            cursor = self.cursor(node)
            for _id, count in counts.items():
                cursor.execute(remove_item_stock_script, (count, _id))
            self.db[node].tpc_prepare()
        except Exception as e:
            raise e
        finally:
            self.db[node].reset()


    def calculate_cost(self, item_ids, node):

        cursor = self.cursor(node)

        counts = dict(collections.Counter(item_ids))

        cursor.execute(calculate_cost_script, (tuple(i for i in item_ids),))
        result = cursor.fetchall()

        available_stock = []
        cost = 0
        for t in result:
            available_stock.append(tuple([t[0], t[2]]))
            cost += counts[t[0]] * t[1]

        return cost, available_stock

    def commit_transaction(self, xid, node):
        self.db[node].tpc_commit(xid)

    def rollback_transaction(self, xid, node):
        self.db[node].tpc_rollback(xid)


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
