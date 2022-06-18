import os
import sys
import time
import uuid

import psycopg2
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient, TopicPartition
from kafka.admin import NewPartitions
from kafka.errors import NoBrokersAvailable

from shared.communication import *
from database import attempt_connect

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
        time.sleep(3)

        self._payment_consumer.assign([TopicPartition(PAYMENT_REQUEST_TOPIC, get_service_id())])
        self._db_connection = attempt_connect()

    def start_listening(self):
        for msg in self._payment_consumer:
            msg_value = msg.value
            _id = msg_value["_id"]
            msg_command = msg_value["command"]
            print(f"Message consumed {_id}")
            try:
                if msg_command == BEGIN_TRANSACTION:
                    msg_obj = msg_value["obj"]
                    self._db_connection.prepare_payment(_id, msg_obj["user_id"], msg_obj["order_id"], msg_obj["amount"])
                elif msg_command == COMMIT_TRANSACTION:
                    self._db_connection.commit_transaction(_id)
                elif msg_command == ROLLBACK_TRANSACTION:
                    print(f"{_id} rollback attempt")
                    self._db_connection.rollback_transaction(_id)
                    print(f"{_id} rollback success")
                    continue
                else:
                    self._payment_producer.send(PAYMENT_RESULTS_TOPIC, fail(_id, msg.value["command"]),
                                                partition=get_service_id())
                    continue
                self._payment_producer.send(PAYMENT_RESULTS_TOPIC, success(_id, msg.value["command"]),
                                            partition=get_service_id())
            except psycopg2.Error as e:
                # print(f"--PAYMENT_{_id}--")
                # print(f"PG Error: {e.pgerror}")
                # print(f"Error: {e}")
                # print(f"Message: {msg_value}")
                # print("-----")
                self._payment_producer.send(PAYMENT_RESULTS_TOPIC, fail(_id, msg.value["command"]),
                                            partition=get_service_id())


def try_connect(retries=3, timeout=2000) -> _Communicator:
    while retries > 0:
        try:
            return _Communicator()
        except NoBrokersAvailable as e:
            print(e)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect kafka broker")
