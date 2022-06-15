from http import client
import os
import sys
import atexit
import time
from uhashring import HashRing

from models import *
from scripts import *

import psycopg2

def connect_to_postgres(db_conf):
    conn = psycopg2.connect(**db_conf)
    return conn

class _DatabaseConnection:

    DATABASE_CLIENTS = {
        "5433": {
            "host": os.environ['POSTGRES_HOST'],
            "port": "5433",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
        "5434": {
            "host": os.environ['POSTGRES_HOST'],
            "port": "5434",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
        "5435": {
            "host": os.environ['POSTGRES_HOST'],
            "port": "5435",
            "database": os.environ['POSTGRES_DB'],
            "user": os.environ['POSTGRES_USER'],
            "password": os.environ['POSTGRES_PASSWORD']
        },
    }

    hash_ring = HashRing(nodes=["5433", "5434", "5435"])

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
        self.cursor(node).execute(create_orders_table)
        self.commit(node)

    def create_order(self, user_id, node):
        cursor = self.cursor(node)
        cursor.execute(create_order_script, (user_id,))
        order = cursor.fetchone()
        self.commit(node)
        return order

    def remove_order(self, order_id, node):
        cursor = self.cursor(node)
        cursor.execute(remove_order_script, (order_id,))
        order = cursor.fetchone()
        self.commit(node)
        return order

    def find_order(self, order_id, node):
        cursor = self.cursor(node)
        cursor.execute(find_order_script, (order_id,))
        order = cursor.fetchone()
        self.commit(node)
        return order

    def add_item(self, order_id, item_id, node):
        cursor = self.cursor(node)
        cursor.execute(add_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit(node)
        return modified_order

    def remove_item(self, order_id, item_id, node):
        cursor = self.cursor(node)
        cursor.execute(remove_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit(node)
        return modified_order

    def update_cost(self, order_id, cost, node):
        cursor = self.cursor(node)
        cursor.execute(update_cost_script, (cost, order_id))
        modified_order = cursor.fetchone()
        self.commit(node)
        return modified_order

    def update_items(self, order_id, items, node):
        cursor = self.cursor(node)
        cursor.execute(update_items_script, (items, order_id))
        modified_order = cursor.fetchone()
        self.commit(node)
        return modified_order

    def update_payment_status(self, order_id, status, node):
        cursor = self.cursor(node)
        cursor.execute(update_payment_status_script, (status, order_id))
        modified_order = cursor.fetchone()
        self.commit(node)
        return modified_order

    def get_node(self, key):
        return self.hash_ring.get(key)["hostname"]

def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e)
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
