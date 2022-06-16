import sys
import time

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from shared.communication import *

import json


class _Communicator:

    def __init__(self):
        self._transaction_producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

        self._results_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_deserializer=lambda x: json.loads(x)
        )
        self._results_consumer.subscribe(topics=[PAYMENT_RESULTS_TOPIC, STOCK_RESULTS_TOPIC])

    def results(self):
        return self._results_consumer

    def start_transaction(self, _id, payment_request: PaymentRequest, stock_request: StockRequest):
        self._transaction_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, BEGIN_TRANSACTION, payment_request)
        )
        self._transaction_producer.send(
            STOCK_REQUEST_TOPIC,
            value=command(_id, BEGIN_TRANSACTION, stock_request)
        )

    def commit_transaction(self, _id):
        self._transaction_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, COMMIT_TRANSACTION)
        )

        self._transaction_producer.send(
            STOCK_REQUEST_TOPIC,
            value=command(_id, COMMIT_TRANSACTION)
        )

    def rollback(self, _id, payment_error, stock_error):
        if not stock_error:
            print(f"ROLLBACK STOCK: {_id}")
            self._transaction_producer.send(
                STOCK_REQUEST_TOPIC,
                value=command(_id, ROLLBACK_TRANSACTION)
            )

        if not payment_error:
            print(f"ROLLBACK PAYMENT: {_id}")
            self._transaction_producer.send(
                PAYMENT_REQUEST_TOPIC,
                value=command(_id, ROLLBACK_TRANSACTION)
            )


def try_connect(retries=3, timeout=2000) -> _Communicator:
    while retries > 0:
        try:
            return _Communicator()
        except NoBrokersAvailable as e:
            print(e)
            retries = retries - 1
            time.sleep(timeout / 1000)
    sys.exit("failed to connect to kafka broker")
