BEGIN_TRANSACTION = 1
ROLLBACK_TRANSACTION = 2
COMMIT_TRANSACTION = 3

SUCCESS = 1
FAIL = 2

PAYMENT_REQUEST_TOPIC = "payment_requests"
PAYMENT_RESULTS_TOPIC = "payment_results"

STOCK_REQUEST_TOPIC = "stock_requests"
STOCK_RESULTS_TOPIC = "stock_results"


def command(_id, command_number, obj=None, shard_attr=None):
    return {
        "_id": _id,
        "command": command_number,
        "shard_attr": shard_attr,
        "obj": obj.__dict__ if obj is not None else None
    }


def success(_id, command_number, shard_attr=None):
    return {
        "_id": _id,
        "command": command_number,
        "res": SUCCESS,
        "shard_attr": shard_attr
    }


def fail(_id, command_number, shard_attr=None):
    return {
        "_id": _id,
        "command": command_number,
        "res": FAIL,
        "shard_attr": shard_attr
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
