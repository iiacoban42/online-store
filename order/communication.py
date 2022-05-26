import sys
import time

from kafka3 import KafkaConsumer
from kafka3 import KafkaProducer
from kafka3.errors import NoBrokersAvailable

from shared.communication import *

import json


class _Communicator:

    def __init__(self):
        self._payment_producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

        self._payment_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_deserializer=lambda x: json.loads(x)
        )
        self._payment_consumer.subscribe([PAYMENT_RESULTS_TOPIC])

    def start_payment(self, _id, payment_request: PaymentRequest):
        self._payment_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, BEGIN_TRANSACTION, payment_request)
        )

    def commit_transaction(self, _id):
        self._payment_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, COMMIT_TRANSACTION)
        )

    def payment_results(self):
        return self._payment_consumer


def try_connect(retries=3, timeout=2000) -> _Communicator:
    while retries > 0:
        try:
            return _Communicator()
        except NoBrokersAvailable as e:
            print(e)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to kafka broker")
