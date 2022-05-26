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


@app.get('/hello')
def hello_world():
    return "<p>Hello, World!</p>"


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
    order = database.add_item(order_id, item_id)
    return order_as_json(order)


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    order = database.remove_item(order_id, item_id)
    return order_as_json(order)


@app.get('/find/<order_id>')
def find_order(order_id):
    order = database.find_order(order_id)
    item_ids = order_as_json(order)["items"]

    cost = coordinator.find(item_ids)
    updated_order = database.update_cost(order_id, cost)

    return order_as_json(updated_order)


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = database.find_order(order_id)
    order_json = order_as_json(order)

    if coordinator.checkout(order_id, order_json["user_id"], order_json["total_cost"]):
        return "success"
    else:
        return "fail"
