import os
import sys
import atexit
import time

import psycopg2

create_script = """
CREATE TABLE IF NOT EXISTS public.Users
(
    user_id bigint NOT NULL,
    credit double precision NOT NULL,
    CONSTRAINT Users_pkey PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS public.Payments
(
    user_id bigint NOT NULL,
    order_id bigint NOT NULL,
    amount double precision NOT NULL,
    payed boolean NOT NULL,
    CONSTRAINT Payments_pkey PRIMARY KEY (user_id, order_id),
    CONSTRAINT Users_fk FOREIGN KEY (user_id)
        REFERENCES public.Users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
"""


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

    def _create_db(self):
        self.db.cursor().execute(create_script)
        self.db.commit()


def attempt_connect(retries=3, timeout=2000) -> _DatabaseConnection:
    while retries > 0:
        try:
            return _DatabaseConnection()
        except psycopg2.Error as e:
            print(e.diag.message_primary)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to database")
