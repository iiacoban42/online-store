class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.credit = 0

    def as_tuple(self):
        return self.user_id, self.credit


class Order:
    def __init__(self, order_id, items, user_id, total_cost):
        self.order_id = order_id
        self.paid = False
        self.items = items
        self.user_id = user_id
        self.total_cost = total_cost

    def as_tuple(self):
        return self.order_id, self.paid, self.items, self.user_id, self.total_cost
