class Order:
    def __init__(self, order_id, items, user_id, total_cost):
        self.order_id = str(order_id)
        self.paid = False
        self.items = [str(x) for x in items]
        self.user_id = str(user_id)
        self.total_cost = total_cost

    def as_tuple(self):
        return self.order_id, self.paid, self.items, self.user_id, self.total_cost
