import os
import sys
import atexit
import time

from models import *
from scripts import *

import psycopg2


class _DatabaseConnection:
    def __init__(self):
        self.db = psycopg2.connect(host=os.environ['POSTGRES_HOST_0'],
                                   port=int(os.environ['POSTGRES_PORT_0']),
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
        self.cursor().execute(create_script)
        self.commit()

    def create_user(self):
        cursor = self.cursor()
        cursor.execute(user_insert_script)
        new_user_id = cursor.fetchone()[0]
        self.commit()
        return new_user_id

    def find_user(self, user_id):
        cursor = self.cursor()
        cursor.execute(user_find_script, (user_id, ))
        user = cursor.fetchone()
        self.commit()
        if user is None:
            return None
        return User(user[0], user[1])

    def add_credit(self, user_id, amount):
        cursor = self.cursor()
        cursor.execute(user_add_credit_script, (amount, user_id))
        modified_item = cursor.fetchone()
        self.commit()
        return modified_item

    def remove_credit(self, user_id, amount):
        try:
            cursor = self.cursor()
            cursor.execute(user_remove_credit_script, (amount, user_id))
            modified_item = cursor.fetchone()
            self.commit()
        except Exception as e:
            raise e
        finally:
            self.db.reset()
        return modified_item

    def create_payment(self, user_id: str, order_id: str, amount: float):
        cursor = self.cursor()
        cursor.execute(payment_insert_script, (user_id, order_id, amount))
        new_payment = cursor.fetchone()
        self.commit()
        return Payment(user_id, order_id, new_payment[2])

    def find_payment(self, user_id, order_id):
        cursor = self.cursor()
        cursor.execute(payment_get_status_script, (user_id, order_id))
        payment = cursor.fetchone()
        self.commit()
        return Payment(user_id, order_id, payment[2])

    def prepare_payment(self, xid, user_id, order_id, amount):
        try:
            self.db.tpc_begin(xid)
            cursor = self.cursor()
            cursor.execute(payment_insert_script, (user_id, order_id, amount))
            cursor.execute(user_remove_credit_script, (amount, user_id))
            self.db.tpc_prepare()
        except Exception as e:
            raise e
        finally:
            self.db.reset()

    def commit_transaction(self, xid):
        self.db.tpc_commit(xid)

    def rollback_transaction(self, xid):
        self.db.tpc_rollback(xid)

    def check_user(self, user_id):
        cursor = self.cursor()
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
