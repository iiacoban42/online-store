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
        self.cursor().execute(create_script)
        self.cursor().execute(user_insert_script)
        self.cursor().execute(user_insert_script)
        self.commit()

    def create_order(self, user_id):
        cursor = self.cursor()
        cursor.execute( f"INSERT INTO public.\"Orders\" "
                        f"(order_id, paid, items, user_id, total_cost) "
                        f"VALUES (DEFAULT, FALSE, '{{}}', {user_id}, 0) RETURNING order_id;")
        new_order_id = cursor.fetchone()[0]
        self.commit()
        return new_order_id


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
