import collections
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
    return order_as_json(order), 200


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    order = database.remove_order(order_id)
    if order is None:
        return f"Order {order_id} was not found.", 400

    return order_as_json(order), 200


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    if database.add_item(order_id, item_id) is None:
        return f"Cannot add items to order: {order_id}. The order was not found or has been placed already.", 400

    return f"Success. Item: {item_id} added to order: {order_id}", 200


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    if database.remove_item(order_id, item_id) is None:
        return f"Cannot remove items from order: {order_id}. The order was not found or has been placed already.", 400

    return f"Success. Item: {item_id}, from order: {order_id} was removed", 200


@app.get('/find/<order_id>')
def find_order(order_id):
    order = database.find_order(order_id)
    if order is None:
        return f"Order {order_id} was not found", 400

    item_ids = order_as_json(order)["items"]
    counts = dict(collections.Counter(item_ids))

    cost = 0
    available_stock = []
    if item_ids != []:
        cost, available_stock = coordinator.find(item_ids)

    updated_order = database.update_cost(order_id, cost)

    filtered_items = []

    items_out_of_stock_ids = []
    items_out_of_stock_values = []

    for (item_id, stock) in available_stock:
        # filter nonexisting items
        filtered_items.extend([item_id] * counts[item_id])
        # check if something is out of stock
        if(stock < counts[item_id]):
            items_out_of_stock_ids.append(item_id)
            items_out_of_stock_values.append(stock)

    if filtered_items != item_ids:
        updated_order = database.update_items(order_id, filtered_items)

    order_json = order_as_json(updated_order)

    if items_out_of_stock_ids != []:
        order_json["not_enough_stock"] = {
        "items": items_out_of_stock_ids,
        "available_stock": items_out_of_stock_values
        }

    return order_json, 200


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order = database.find_order(order_id)
    if order is None:
        return f"Order {order_id} was not found. Cannot process checkout.", 400

    order_json = order_as_json(order)
    item_ids = order_json["items"]

    if item_ids == []:
        return f"Order {order_id} does not contain any items.", 400

    payment_checkout =  coordinator.payment_checkout(order_id, order_json["user_id"], order_json["total_cost"])
    stock_checkout = coordinator.stock_checkout(order_id, item_ids)

    if payment_checkout:
        order_json["paid"] = True
        database.update_payment_status(order_id, True)

    if payment_checkout and stock_checkout:
        return f"Success. Order {order_id} was placed.", 200
    elif payment_checkout and not stock_checkout:
        return f"Stock service failed when attempting to place order {order_id}.", 400
    elif not payment_checkout and stock_checkout:
        return f"Payment service failed when attempting to place order {order_id}.", 400
    else:
        return f"Payment and Stock serviced failed when attempting to place order {order_id}.", 400
