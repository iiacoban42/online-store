import os
import sys
import atexit
import time
import uuid

from scripts import *

import psycopg2

from uhashring import HashRing
import psycopg2.extras

class _DatabaseConnection:
    def __init__(self):
        self.dbs: dict = {'node1': psycopg2.connect(host=os.environ['POSTGRES_HOST_0'],
                                                    port=int(os.environ['POSTGRES_PORT_0']),
                                                    user=os.environ['POSTGRES_USER'],
                                                    password=os.environ['POSTGRES_PASSWORD'],
                                                    database=int(os.environ['POSTGRES_DB'])),
                          'node2': psycopg2.connect(host=os.environ['POSTGRES_HOST_1'],
                                                    port=int(os.environ['POSTGRES_PORT_1']),
                                                    user=os.environ['POSTGRES_USER'],
                                                    password=os.environ['POSTGRES_PASSWORD'],
                                                    database=int(os.environ['POSTGRES_DB'])),
                          'node3': psycopg2.connect(host=os.environ['POSTGRES_HOST_2'],
                                                    port=int(os.environ['POSTGRES_PORT_2']),
                                                    user=os.environ['POSTGRES_USER'],
                                                    password=os.environ['POSTGRES_PASSWORD'],
                                                    database=int(os.environ['POSTGRES_DB']))}
        self.__create_dbs()
        psycopg2.extras.register_uuid()
        atexit.register(self._close_db_connection)

        self.hash_ring = HashRing(nodes=list(self.dbs.keys()))

    def _close_db_connection(self):
        for x in self.dbs.values():
            x.close()

    def cursor(self, shard_id):
        return self.dbs[shard_id].cursor()

    def commit(self, shard_id):
        self.dbs[shard_id].commit()

    def __create_dbs(self):
        for shard_id in self.dbs.keys():
            self.__create_db(shard_id)

    def __create_db(self, shard_id):
        cursor = self.cursor(shard_id)
        cursor.execute(create_orders_table)
        self.commit(shard_id)

    def create_order(self, user_id):
        _id = str(uuid.uuid4())
        shard_id = self.hash_ring.get_node(_id)

        cursor = self.cursor(shard_id)
        cursor.execute(create_order_script, (_id, user_id))
        order = cursor.fetchone()
        self.commit(shard_id)
        return order

    def remove_order(self, order_id):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(remove_order_script, (order_id,))
        order = cursor.fetchone()
        self.commit(shard_id)
        return order

    def find_order(self, order_id):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(find_order_script, (order_id,))
        order = cursor.fetchone()
        self.commit(shard_id)
        return order

    def add_item(self, order_id, item_id):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(add_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit(shard_id)
        return modified_order

    def remove_item(self, order_id, item_id):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(remove_item_script, (item_id, order_id))
        modified_order = cursor.fetchone()
        self.commit(shard_id)
        return modified_order

    def update_cost(self, order_id, cost):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(update_cost_script, (cost, order_id))
        modified_order = cursor.fetchone()
        self.commit(shard_id)
        return modified_order

    def update_items(self, order_id, items):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(update_items_script, (items, order_id))
        modified_order = cursor.fetchone()
        self.commit(shard_id)
        return modified_order

    def update_payment_status(self, order_id, status):
        shard_id = self.hash_ring.get_node(order_id)

        cursor = self.cursor(shard_id)
        cursor.execute(update_payment_status_script, (status, order_id))
        modified_order = cursor.fetchone()
        self.commit(shard_id)
        return modified_order


def attempt_connect(retries=3, timeout=15000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
