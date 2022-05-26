class User:
    def __init__(self, user_id, credit=0):
        self.user_id = user_id
        self.credit = credit

    def as_tuple(self):
        return self.user_id, self.credit


class Payment:
    def __init__(self, user_id, order_id, amount):
        self.user_id = user_id
        self.order_id = order_id
        self.amount = amount

    def as_tuple(self):
        return self.user_id, self.order_id, self.amount
