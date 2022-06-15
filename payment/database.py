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
        self.cursor(node).execute(create_script)
        self.commit(node)

    def create_user(self, node):
        cursor = self.cursor(node)
        cursor.execute(user_insert_script)
        new_user_id = cursor.fetchone()[0]
        self.commit(node)
        return new_user_id

    def find_user(self, user_id, node):
        cursor = self.cursor(node)
        cursor.execute(user_find_script, (user_id, ))
        user = cursor.fetchone()
        self.commit(node)
        if user is None:
            return None
        return User(user[0], user[1])

    def add_credit(self, user_id, amount, node):
        cursor = self.cursor(node)
        cursor.execute(user_add_credit_script, (amount, user_id))
        self.commit(node)

    def remove_credit(self, user_id, amount, node):
        cursor = self.cursor(node)
        cursor.execute(user_remove_credit_script, (amount, user_id))
        credit = cursor.fetchone()[0]
        self.commit(node)
        return credit

    def create_payment(self, user_id: str, order_id: str, amount: int, node):
        cursor = self.cursor(node)
        cursor.execute(payment_insert_script, (user_id, order_id, amount))
        new_payment = cursor.fetchone()
        self.commit(node)
        return Payment(user_id, order_id, new_payment[2])

    def find_payment(self, user_id, order_id, node):
        cursor = self.cursor(node)
        cursor.execute(payment_get_status_script, (user_id, order_id))
        payment = cursor.fetchone()
        self.commit(node)
        return Payment(user_id, order_id, payment[2])

    def prepare_payment(self, xid, user_id, order_id, amount, node):
        try:
            self.db[node].tpc_begin(xid)
            cursor = self.cursor(node)
            cursor.execute(payment_insert_script, (user_id, order_id, amount))
            cursor.execute(user_remove_credit_script, (amount, user_id))
            self.db[node].tpc_prepare()
        except Exception as e:
            raise e
        finally:
            self.db[node].reset()

    def commit_transaction(self, xid, node):
        self.db[node].tpc_commit(xid)

    def rollback_transaction(self, xid, node):
        self.db[node].tpc_rollback(xid)

    def check_user(self, user_id, node):
        cursor = self.cursor(node)
        cursor.execute(check_user_script, (user_id,))
        result = cursor.fetchone()[0]
        if result == 1:
            return True

        return False


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
