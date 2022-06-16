import sys
import time

import psycopg2
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from shared.communication import *
from database import attempt_connect

import json

import hashlib

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

                    shard_and_items = {}  # {shard: items_in_shard}

                    for item_id in item_ids:

                        hashed = hashlib.shake_256(str(item_id).encode())
                        shortened = hashed.digest(6)
                        shard = self._db_connection.get_node(shortened)

                        if shard not in shard_and_items:
                            shard_and_items[shard] = [item_id]
                        else:
                            shard_and_items[shard].append(item_id)

                    item_counts_per_shard = {}

                    for shard, items in shard_and_items.items():
                        for item_id in items:
                            if shard not in item_counts_per_shard:
                                item_counts_per_shard[shard] = {item_id: counts[item_id]}
                            else:
                                item_counts_per_shard[shard][item_id] = counts[item_id]

                    for node, shard_counts in item_counts_per_shard.items():
                        self._db_connection.remove_stock_request(_id, shard_counts, node)

                elif msg_command == COMMIT_TRANSACTION:
                    self._db_connection.commit_transaction(_id)
                elif msg_command == ROLLBACK_TRANSACTION:
                    self._db_connection.rollback_transaction(_id)
                else:
                    self._stock_producer.send(STOCK_RESULTS_TOPIC, fail(_id, msg.value["command"]))
                    return
                self._stock_producer.send(STOCK_RESULTS_TOPIC, success(_id, msg.value["command"]))
            except psycopg2.Error as e:
                print(f"--STOCK_{_id}--")
                print(f"PG Error: {e.pgerror}")
                print(f"Error: {e}")
                print(f"Message: {msg_value}")
                print("-----")
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
