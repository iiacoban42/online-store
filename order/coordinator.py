import threading
import uuid
import time
from enum import Flag

import communication
import shared.communication as sc


class Status(Flag):
    STARTED = 512
    ERROR = 1
    PAYMENT_PREPARED = 2
    PAYMENT_COMMITTED = 4
    STOCK_PREPARED = 8
    STOCK_COMMITTED = 16
    ROLLBACK_SENT = 32
    COMMIT_SENT = 64
    PAYMENT_FAIL = 128
    STOCK_FAIL = 256
    FINISHED = PAYMENT_COMMITTED | STOCK_COMMITTED
    READY_FOR_COMMIT = PAYMENT_PREPARED | STOCK_PREPARED
    STOCK_ROLLBACK = STOCK_PREPARED | PAYMENT_FAIL
    PAYMENT_ROLLBACK = STOCK_FAIL | PAYMENT_PREPARED
    FULL_FAIL = STOCK_FAIL | PAYMENT_FAIL

    def has_flag(self, flag: Flag):
        return self & flag == flag


class Coordinator:
    def __init__(self):
        self.communicator = communication.try_connect(timeout=5000)
        self.running_requests = {}
        self.result_func_dict = {
            sc.PAYMENT_RESULTS_TOPIC: lambda msg: self.handle_payment_result(msg),
            sc.STOCK_RESULTS_TOPIC: lambda msg: self.handle_stock_result(msg)
        }

        threading.Thread(target=lambda: self.listen_results()).start()

    def listen_results(self):
        results_consumer = self.communicator.results()
        while True:
            try:
                topic_queues = results_consumer.poll(5000)
                if not topic_queues:
                    results_consumer.topics()
                    continue
                for message_queue in topic_queues.values():
                    for msg in message_queue:
                        self.result_func_dict[msg.topic](msg)
            except Exception as e:
                print(f"LISTENING exception: {type(e).__name__} {e}")

    def handle_payment_result(self, result):
        try:
            result_obj = result.value
            _id = result_obj["_id"]
            self.set_new_state_payment(_id, result_obj)
            self.do_next_action(_id)
        except KeyError:
            print(f"Key Error payment ---------------")
            print(result)
            print("--------------------------")

    def handle_stock_result(self, result):
        try:
            result_obj = result.value
            _id = result_obj["_id"]
            self.set_new_state_stock(_id, result_obj)
            self.do_next_action(_id)
        except KeyError:
            print(f"Key Error stock ---------------")
            print(result)
            print("--------------------------")

    def set_new_state_payment(self, _id, res_obj):
        result = res_obj["res"]
        if result == sc.SUCCESS:
            if res_obj["command"] == sc.BEGIN_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_PREPARED
            elif res_obj["command"] == sc.COMMIT_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_COMMITTED
        elif result == sc.FAIL:
            print(f"FAIL payment: {_id} for {Status(res_obj['command'])}")
            self.running_requests[_id] |= Status.PAYMENT_FAIL

    def set_new_state_stock(self, _id, res_obj):
        result = res_obj["res"]
        if result == sc.SUCCESS:
            if res_obj["command"] == sc.BEGIN_TRANSACTION:
                self.running_requests[_id] |= Status.STOCK_PREPARED
            elif res_obj["command"] == sc.COMMIT_TRANSACTION:
                self.running_requests[_id] |= Status.STOCK_COMMITTED
        elif result == sc.FAIL:
            print(f"FAIL stock: {_id} for {Status(res_obj['command'])}")
            self.running_requests[_id] |= Status.STOCK_FAIL

    def do_next_action(self, _id):
        state = self.running_requests[_id]
        if (state.has_flag(Status.STOCK_ROLLBACK) or state.has_flag(Status.PAYMENT_ROLLBACK)) and not state.has_flag(Status.ROLLBACK_SENT):
            self.communicator.rollback(_id, state.has_flag(Status.PAYMENT_FAIL), state.has_flag(Status.STOCK_FAIL))
            self.running_requests[_id] |= Status.ROLLBACK_SENT | Status.ERROR
            return
        if state.has_flag(Status.FULL_FAIL):
            self.running_requests[_id] |= Status.ERROR
        if state.has_flag(Status.FINISHED):
            print(f"FINISHED: {_id}")
            return
        if state.has_flag(Status.READY_FOR_COMMIT) and not state.has_flag(Status.COMMIT_SENT):
            print(f"COMMIT: {_id}")
            self.communicator.commit_transaction(_id)
            self.running_requests[_id] |= Status.COMMIT_SENT

    def checkout(self, order_id, item_ids, user_id, amount):
        _id = str(uuid.uuid4())
        self.running_requests[_id] = Status.STARTED
        self.communicator.start_transaction(_id,
                                            sc.PaymentRequest(order_id, user_id, amount),
                                            sc.StockRequest(order_id, item_ids))
        return _id

    def rollback_open_transactions(self, _id):
        state = self.running_requests[_id]

        if state.has_flag(Status.ERROR) or state.has_flag(Status.FINISHED):
            return

        payment_error = True
        stock_error = True

        if state.has_flag(Status.PAYMENT_PREPARED) \
                and not (state.has_flag(Status.PAYMENT_ROLLBACK) or state.has_flag(Status.PAYMENT_COMMITTED)):
            payment_error = False
        if state.has_flag(Status.STOCK_PREPARED) \
                and not (state.has_flag(Status.STOCK_ROLLBACK) or state.has_flag(Status.STOCK_COMMITTED)):
            stock_error = False

        if not (payment_error and stock_error):
            self.communicator.rollback(_id, payment_error, stock_error)

    def wait_result(self, _id, timeout=5):
        t_end = time.monotonic() + timeout
        result = False
        print(f"---{_id}--")
        while time.monotonic() < t_end:
            state = self.running_requests[_id]
            if _id not in self.running_requests:
                return result
            if state.has_flag(Status.ERROR | Status.ROLLBACK_SENT):
                print(f"final state: {self.running_requests[_id]}")
                break
            if state.has_flag(Status.FINISHED):
                result = True
                break

        self.rollback_open_transactions(_id)
        self.running_requests.pop(_id)
        return result
