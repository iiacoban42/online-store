import threading
import uuid
import time
from enum import Flag

import communication
import shared.communication as sc


class Status(Flag):
    STARTED = 0
    ERROR = 1
    PAYMENT_READY = 2
    PAYMENT_COMMITTED = 4
    FINISHED = 8
    STOCK_READY = 16
    STOCK_COMMITTED = 32


class Coordinator:
    def __init__(self):
        self.communicator = communication.try_connect(timeout=5000)
        self.running_requests = {}

        threading.Thread(target=lambda: self.listen_results()).start()

    def listen_results(self):
        for result in self.communicator.payment_results():
            _id = result.value["_id"]
            if result.value["res"] == sc.SUCCESS and self.running_requests[_id] & (
                    Status.PAYMENT_READY | Status.STOCK_READY):
                self.running_requests[_id] = self.running_requests[_id] | Status.FINISHED
            elif result.value["res"] == sc.FAIL:
                self.running_requests[_id] = self.running_requests[_id] | Status.ERROR

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
