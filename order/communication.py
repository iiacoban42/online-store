import sys
import time

from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from kafka.admin import NewTopic
from kafka.errors import NoBrokersAvailable
from kafka import KafkaAdminClient
from kafka.admin.new_partitions import NewPartitions
import json
from shared.communication import *
from kafka import KafkaClient
TOPICS = [PAYMENT_RESULTS_TOPIC, STOCK_RESULTS_TOPIC, PAYMENT_REQUEST_TOPIC, STOCK_REQUEST_TOPIC]


class _Communicator:

    def __init__(self):
        if get_service_id() == 0:
            client = KafkaAdminClient(bootstrap_servers='kafka:9092')

            diff = list(set(TOPICS) - set())
            r = [NewTopic(x, NUMBER_OF_PARTITIONS, 1) for x in diff]
            client.create_topics(new_topics=r)
            print(f"Created topics: {diff}")

        self._transaction_producer = KafkaProducer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        )

        self._results_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="order_service",
            value_deserializer=lambda x: json.loads(x)
        )

        if get_service_id() != 0:
            time.sleep(3)

        self._results_consumer.assign([TopicPartition(PAYMENT_RESULTS_TOPIC, get_service_id()),
                                       TopicPartition(STOCK_RESULTS_TOPIC, get_service_id())])

    def results(self):
        return self._results_consumer

    def start_transaction(self, _id, payment_request: PaymentRequest, stock_request: StockRequest):
        _payment_consumer = KafkaConsumer(
            bootstrap_servers="kafka:9092",
            client_id="payment_service",
            value_deserializer=lambda x: json.loads(x)
        )

        print(f"PAY PARTS: {_payment_consumer.partitions_for_topic(PAYMENT_REQUEST_TOPIC)}")
        print(f"STOCK PARTS: {_payment_consumer.partitions_for_topic(STOCK_REQUEST_TOPIC)}")
        self._transaction_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, BEGIN_TRANSACTION, payment_request),
            partition=get_service_id()
        )
        self._transaction_producer.send(
            STOCK_REQUEST_TOPIC,
            value=command(_id, BEGIN_TRANSACTION, stock_request),
            partition=get_service_id()
        )

    def commit_transaction(self, _id):
        self._transaction_producer.send(
            PAYMENT_REQUEST_TOPIC,
            value=command(_id, COMMIT_TRANSACTION),
            partition=get_service_id()
        )

        self._transaction_producer.send(
            STOCK_REQUEST_TOPIC,
            value=command(_id, COMMIT_TRANSACTION),
            partition=get_service_id()
        )

    def rollback(self, _id, payment_error, stock_error):
        if not stock_error:
            print(f"ROLLBACK STOCK: {_id}")
            self._transaction_producer.send(
                STOCK_REQUEST_TOPIC,
                value=command(_id, ROLLBACK_TRANSACTION),
                partition=get_service_id()
            )

        if not payment_error:
            print(f"ROLLBACK PAYMENT: {_id}")
            self._transaction_producer.send(
                PAYMENT_REQUEST_TOPIC,
                value=command(_id, ROLLBACK_TRANSACTION),
                partition=get_service_id()
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
