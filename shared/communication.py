import itertools
import os

BEGIN_TRANSACTION = 1
ROLLBACK_TRANSACTION = 2
COMMIT_TRANSACTION = 3

SUCCESS = 1
FAIL = 2

PAYMENT_REQUEST_TOPIC = "payment_requests"
PAYMENT_RESULTS_TOPIC = "payment_results"

STOCK_REQUEST_TOPIC = "stock_requests"
STOCK_RESULTS_TOPIC = "stock_results"

NUMBER_OF_PARTITIONS = 4


def get_service_id():
    return int(os.environ["SERVICE_ID"])


def command(_id, command_number, obj=None):
    return {
        "_id": _id,
        "command": command_number,
        "obj": obj.__dict__ if obj is not None else None
    }


def success(_id, command_number):
    return {
        "_id": _id,
        "command": command_number,
        "res": SUCCESS
    }


def fail(_id, command_number):
    return {
        "_id": _id,
        "command": command_number,
        "res": FAIL
    }


class PaymentRequest:
    def __init__(self, order_id, user_id, amount):
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount


class StockRequest:
    def __init__(self, order_id, item_ids):
        self.order_id = order_id
        self.item_ids = item_ids
