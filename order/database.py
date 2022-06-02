import os
import sys
import atexit
import time

from models import *
from scripts import *

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
        self.cursor().execute(create_orders_table)
        self.commit()

    def create_order(self, user_id):
        cursor = self.cursor()
        cursor.execute(create_order_script, (user_id))
        new_order_id = cursor.fetchone()[0]
        self.commit()
        return self.find_order(new_order_id)

    def remove_order(self, order_id):
        order = self.find_order(order_id)
        cursor = self.cursor()
        cursor.execute(remove_order_script, (order_id,))
        self.commit()
        return order

    def find_order(self, order_id):
        cursor = self.cursor()
        cursor.execute(find_order_script, (order_id,))
        order = cursor.fetchone()
        self.commit()
        return order

    def add_item(self, order_id, item_id):
        cursor = self.cursor()
        cursor.execute(add_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit()
        return modified_order

    def remove_item(self, order_id, item_id):
        cursor = self.cursor()
        cursor.execute(remove_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit()
        return modified_order

    def update_cost(self, order_id, cost):
        cursor = self.cursor()
        cursor.execute(update_cost_script, (cost, order_id))
        self.commit()
        return self.find_order(order_id)

    def update_items(self, order_id, items):
        cursor = self.cursor()
        cursor.execute(update_items_script, (items, order_id))
        self.commit()
        return self.find_order(order_id)

    def update_payment_status(self, order_id, status):
        cursor = self.cursor()
        cursor.execute(update_payment_status_script, (status, order_id))
        self.commit()
        return self.find_order(order_id)

def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
