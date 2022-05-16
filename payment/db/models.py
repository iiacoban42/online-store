class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.credit = 0


class Payment:
    def __init__(self, user_id, order_id, amount):
        self.user_id = user_id
        self.order_id = order_id
        self.amount = amount
        self.payed = False
