BEGIN_TRANSACTION = 1
ROLLBACK_TRANSACTION = 2
COMMIT_TRANSACTION = 3

SUCCESS = 1
FAIL = 2


def command(_id, command_number, obj=None):
    return {
        "id": _id,
        "command": command_number,
        "obj": obj.__dict__ if obj is not None else None
    }


def success(_id):
    return {
        "_id": _id,
        "res": SUCCESS
    }


class PaymentRequest:
    def __init__(self, order_id, user_id, amount):
        self.order_id = order_id
        self.user_id = user_id
        self.amount = amount
