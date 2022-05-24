import threading
import uuid
import time
from enum import Flag

import communication
import shared.communication as sc


class Status(Flag):
    STARTED = 0
    ERROR = 1
    PAYMENT_PREPARED = 2
    PAYMENT_COMMITTED = 4
    STOCK_PREPARED = 8
    STOCK_COMMITTED = 16
    FINISHED = ~ERROR & PAYMENT_COMMITTED
    READY_FOR_COMMIT = ~ERROR & PAYMENT_PREPARED & ~PAYMENT_COMMITTED

    def has_flag(self, flag: Flag):
        return self & flag == flag


class Coordinator:
    def __init__(self):
        self.communicator = communication.try_connect(timeout=5000)
        self.running_requests = {}

        threading.Thread(target=lambda: self.listen_results()).start()

    def listen_results(self):
        for result in self.communicator.payment_results():
            result_obj = result.value
            _id = result_obj["_id"]
            self.set_new_state(_id, result_obj)
            self.do_next_action(_id)

    def set_new_state(self, _id, res_obj):
        result = res_obj["res"]
        if result == sc.SUCCESS:
            if res_obj["command"] == sc.BEGIN_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_PREPARED
            elif res_obj["command"] == sc.COMMIT_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_COMMITTED
        elif result == sc.FAIL:
            self.running_requests[_id] |= Status.ERROR

    def do_next_action(self, _id):
        state = self.running_requests[_id]
        if state.has_flag(Status.FINISHED):
            return
        if state.has_flag(Status.ERROR):
            return  # TODO: ROLLBACK
        if state.has_flag(Status.READY_FOR_COMMIT):
            self.communicator.commit_transaction(_id)

    def checkout(self, order_id, user_id, amount):
        _id = str(uuid.uuid4())
        self.running_requests[_id] = Status.STARTED
        self.communicator.start_payment(_id, sc.PaymentRequest(order_id, user_id, amount))
        return self.wait_result(_id)

    def wait_result(self, _id, timeout=5000):
        start = time.time() * 1000
        while time.time() * 1000 < start + timeout:
            if _id not in self.running_requests:
                return False
            if self.running_requests[_id] & Status.ERROR:
                return False
            if self.running_requests[_id] & Status.FINISHED:
                return True
        return False
