import sys
import time

import psycopg2
from kafka3 import KafkaConsumer
from kafka3 import KafkaProducer
from kafka3.errors import NoBrokersAvailable

from shared.communication import *
from database import attempt_connect

import json

import collections


class _Communicator:

    def __init__(self):
        self._stock_producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="stock_service",
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

        self._stock_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="stock_service",
            value_deserializer=lambda x: json.loads(x)
        )
        self._stock_consumer.subscribe([STOCK_REQUEST_TOPIC])
        self._db_connection = attempt_connect()

    def start_listening(self):
        for msg in self._stock_consumer:
            msg_value = msg.value
            _id = msg_value["_id"]
            msg_command = msg_value["command"]
            try:
                if msg_command == BEGIN_TRANSACTION:
                    msg_obj = msg_value["obj"]
                    item_ids = msg_obj["item_ids"]
                    counts = dict(collections.Counter(item_ids))
                    for i in counts:
                        self._db_connection.remove_stock_request(_id, i, counts[i])
                if msg_command == REQUEST_COST:
                    msg_obj = msg_value["obj"]
                    cost = self._db_connection.calculate_cost(_id, msg_obj["item_ids"])
                    self._stock_producer.send(STOCK_RESULTS_TOPIC, reply(_id, REPLY, cost))
                if msg_command == COMMIT_TRANSACTION:
                    self._db_connection.commit_transaction(_id)
                if msg_command == ROLLBACK_TRANSACTION:
                    self._db_connection.rollback_transaction(_id)
                self._stock_producer.send(STOCK_RESULTS_TOPIC, success(_id, msg.value["command"]))
            except psycopg2.Error as e:
                print(e.pgerror)
                self._stock_producer.send(STOCK_RESULTS_TOPIC, fail(_id, msg.value["command"]))


def try_connect(retries=3, timeout=2000) -> _Communicator:
    while retries > 0:
        try:
            return _Communicator()
        except NoBrokersAvailable as e:
            print(e)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect kafka broker")
