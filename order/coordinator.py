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
    ROLLBACK_SENT = 32
    COMMIT_SENT = 64
    FINISHED = PAYMENT_COMMITTED | STOCK_COMMITTED
    READY_FOR_COMMIT = PAYMENT_PREPARED | STOCK_PREPARED

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

        # TODO: Announce yourself -> send message to cancel any open transaction maybe? (for when order crashes)
        threading.Thread(target=lambda: self.listen_results()).start()

    def listen_results(self):
        results_consumer = self.communicator.results()
        print("listening")
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
                print(e)

    def handle_payment_result(self, result):
        result_obj = result.value
        _id = result_obj["_id"]
        self.set_new_state_payment(_id, result_obj)
        self.do_next_action(_id)

    def handle_stock_result(self, result):
        result_obj = result.value
        _id = result_obj["_id"]
        self.set_new_state_stock(_id, result_obj)
        self.do_next_action(_id)

    def set_new_state_payment(self, _id, res_obj):
        result = res_obj["res"]
        if result == sc.SUCCESS:
            if res_obj["command"] == sc.BEGIN_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_PREPARED
            elif res_obj["command"] == sc.COMMIT_TRANSACTION:
                self.running_requests[_id] |= Status.PAYMENT_COMMITTED
        elif result == sc.FAIL:
            print(f"payment error for command {res_obj['command']}")
            self.running_requests[_id] |= Status.ERROR

    def set_new_state_stock(self, _id, res_obj):
        result = res_obj["res"]
        if result == sc.SUCCESS:
            if res_obj["command"] == sc.BEGIN_TRANSACTION:
                self.running_requests[_id] |= Status.STOCK_PREPARED
            elif res_obj["command"] == sc.COMMIT_TRANSACTION:
                self.running_requests[_id] |= Status.STOCK_COMMITTED
        elif result == sc.FAIL:
            print(f"stock error for command {res_obj['command']}")
            self.running_requests[_id] |= Status.ERROR

    def do_next_action(self, _id):
        state = self.running_requests[_id]
        print(state)
        if state.has_flag(Status.ERROR) and not state.has_flag(Status.ROLLBACK_SENT):
            print("rolling back")
            self.communicator.rollback(_id)
            self.running_requests[_id] |= Status.ROLLBACK_SENT
            return
        if state.has_flag(Status.FINISHED):
            print("finished")
            return
        if state.has_flag(Status.READY_FOR_COMMIT) and not state.has_flag(Status.COMMIT_SENT):
            print("committing")
            self.communicator.commit_transaction(_id)
            self.running_requests[_id] |= Status.COMMIT_SENT

    def checkout(self, order_id, item_ids, user_id, amount):
        _id = str(uuid.uuid4())
        self.running_requests[_id] = Status.STARTED
        self.communicator.start_payment(_id, sc.PaymentRequest(order_id, user_id, amount))
        self.communicator.start_remove_stock(_id, sc.StockRequest(order_id, item_ids))
        return _id

    def wait_result(self, _id, timeout=5000):
        start = time.time() * 1000
        result = False
        while time.time() * 1000 < start + timeout:
            state = self.running_requests[_id]
            if _id not in self.running_requests:
                return result
            if state.has_flag(Status.ERROR | Status.ROLLBACK_SENT):
                break
            if state.has_flag(Status.FINISHED):
                result = True
                break
        # TODO: Timeout -> check for any open transactions and roll them back
        self.running_requests.pop(_id)
        return result
