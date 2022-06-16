import sys
import time

import psycopg2
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from shared.communication import *
from database import attempt_connect

import hashlib

import json


class _Communicator:

    def __init__(self):
        self._payment_producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="payment_service",
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

        self._payment_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="payment_service",
            value_deserializer=lambda x: json.loads(x)
        )
        self._payment_consumer.subscribe([PAYMENT_REQUEST_TOPIC])
        self._db_connection = attempt_connect()

    def start_listening(self):
        for msg in self._payment_consumer:
            msg_value = msg.value
            _id = msg_value["_id"]
            msg_command = msg_value["command"]
            try:
                if msg_command == BEGIN_TRANSACTION:
                    msg_obj = msg_value["obj"]
                    user_id = msg_obj["user_id"]
                    hashed = hashlib.shake_256(str(user_id).encode())
                    shortened = hashed.digest(6)
                    node = self._db_connection.get_node(shortened)
                    self._db_connection.prepare_payment(_id, msg_obj["user_id"], msg_obj["order_id"], msg_obj["amount"], node)
                elif msg_command == COMMIT_TRANSACTION:
                    self._db_connection.commit_transaction(_id)
                elif msg_command == ROLLBACK_TRANSACTION:
                    self._db_connection.rollback_transaction(_id)
                else:
                    self._payment_producer.send(PAYMENT_RESULTS_TOPIC, fail(_id, msg.value["command"]))
                    return
                self._payment_producer.send(PAYMENT_RESULTS_TOPIC, success(_id, msg.value["command"]))
            except psycopg2.Error as e:
                print(f"--PAYMENT_{_id}--")
                print(f"PG Error: {e.pgerror}")
                print(f"Error: {e}")
                print(f"Message: {msg_value}")
                print("-----")
                self._payment_producer.send(PAYMENT_RESULTS_TOPIC, fail(_id, msg.value["command"]))


def try_connect(retries=3, timeout=2000) -> _Communicator:
    while retries > 0:
        try:
            return _Communicator()
        except NoBrokersAvailable as e:
            print(e)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect kafka broker")
