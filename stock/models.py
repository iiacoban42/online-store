class Item:
    def __init__(self, item_id, price = 0,stock=0):
        self.item_id = item_id
        self.price = price
        self.stock = stock

    def as_tuple(self):
        return self.item_id, self.price, self.stock
