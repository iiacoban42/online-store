from flask import Flask
from database import *
from coordinator import Coordinator


app = Flask("order-service")
database = attempt_connect()
coordinator = Coordinator()


def order_as_json(order):
    return {
        "order_id": order[0],
        "paid": order[1],
        "items": order[2],
        "user_id": order[3],
        "total_cost": order[4]
    }


@app.post('/create/<user_id>')
def create_order(user_id):
    order = database.create_order(user_id)
    return order_as_json(order)


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    order = database.remove_order(order_id)
    return order_as_json(order)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    database.add_item(order_id, item_id)
    return "success"


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    database.remove_item(order_id, item_id)
    return "success"


@app.get('/find/<order_id>')
def find_order(order_id):
    order = database.find_order(order_id)
    item_ids = order_as_json(order)["items"]

    cost = 0
    if item_ids != []:
        cost = coordinator.find(item_ids)

    updated_order = database.update_cost(order_id, cost)
    return order_as_json(updated_order)


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = database.find_order(order_id)
    order_json = order_as_json(order)
    item_ids = order_json["items"]

    payment_checkout =  coordinator.payment_checkout(order_id, order_json["user_id"], order_json["total_cost"])
    stock_checkout = coordinator.stock_checkout(order_id, item_ids)

    if payment_checkout:
        order_json["paid"] = True
        database.update_payment_status(order_id, True)

    if payment_checkout and stock_checkout:
        return "success"
    elif payment_checkout and not stock_checkout:
        return "fail at stock"
    elif not payment_checkout and stock_checkout:
        return "fail at payment"
    else:
        return "fail at both"
