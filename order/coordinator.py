import threading
import uuid
import time

import communication
from shared.communication import PaymentRequest


class Coordinator:
    def __init__(self):
        self.communicator = communication.try_connect(timeout=5000)
        self.running_requests = {}

        threading.Thread(target=lambda x: self.listen_results()).start()

    def listen_results(self):
        for result in self.communicator.payment_results():


    def checkout(self, order_id):
        _id = uuid.uuid4()
        self.communicator.start_payment(_id, PaymentRequest(1, 1, 1))
        # self.running_requests[_id] =
        start_time = time.time()

