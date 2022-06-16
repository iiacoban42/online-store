import collections
import requests
import json
from flask import Flask
import hashlib
from database import *
from coordinator import Coordinator
import os

app = Flask("order-service")
database = attempt_connect()
coordinator = Coordinator()

BACKUP_FILE = os.getcwd() + "/order_id.json"

with open(BACKUP_FILE, "r", encoding="utf8") as file:
    ORDER_ID = json.load(file)


def increment_id():
    ORDER_ID["order_id"] += 1
    with open(BACKUP_FILE, "w", encoding="utf8") as file:
        json.dump(ORDER_ID, file)


def order_as_json(order):
    return {
        "order_id": order[0],
        "paid": order[1],
        "items": order[2],
        "user_id": order[3],
        "total_cost": order[4]
    }


def get_shard(order_id):
    hashed = hashlib.shake_256(order_id.encode())
    # Get 6 character order_id hash
    shortened = hashed.digest(6)
    # use the order_id to get a node key
    node = database.get_node(shortened)
    return node


@app.post('/create/<user_id>')
def create_order(user_id):
    if user_id is not None:
        request = "http://host.docker.internal:5300/check_user/" + user_id
        response = requests.get(request)

        content = response.content

        content_as_dict = json.loads(content.decode('utf-8'))
        user_exists = content_as_dict['user_exists']

        if user_exists:
            order_id = ORDER_ID["order_id"]
            node = get_shard(order_id)

            order = database.create_order(user_id, order_id, node)
            increment_id()
            return order_as_json(order), 200

    return f"User {user_id} was not found.", 400


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    node = get_shard(order_id)
    order = database.remove_order(order_id, node)
    if order is None:
        return f"Order {order_id} was not found.", 400

    return order_as_json(order), 200


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    node = get_shard(order_id)
    if database.add_item(order_id, item_id, node) is None:
        return f"Cannot add items to order: {order_id}. The order was not found or has been placed already.", 400

    return f"Success. Item: {item_id} added to order: {order_id}", 200


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    node = get_shard(order_id)
    if database.remove_item(order_id, item_id, node) is None:
        return f"Cannot remove items from order: {order_id}. The order was not found or has been placed already.", 400

    return f"Success. Item: {item_id}, from order: {order_id} was removed", 200


@app.get('/find/<order_id>')
def find_order(order_id):
    node = get_shard(order_id)
    order = database.find_order(order_id, node)
    if order is None:
        return f"Order {order_id} was not found", 400

    item_ids = order_as_json(order)["items"]
    counts = dict(collections.Counter(item_ids))

    cost = 0
    available_stock = []

    if item_ids:

        items = ""
        for i in item_ids:
            items += str(i) + ","
        items = items[:len(items) - 1]
        request = "http://host.docker.internal:5200/calculate_cost/" + items

        response = requests.get(request)

        content = response.content

        content_as_dict = json.loads(content.decode('utf-8'))
        cost = content_as_dict['cost']
        available_stock = content_as_dict['available_stock']

    updated_order = database.update_cost(order_id, cost)

    filtered_items = []

    items_out_of_stock_ids = []
    items_out_of_stock_values = []

    for (item_id, stock) in available_stock:
        # filter nonexisting items
        filtered_items.extend([item_id] * counts[item_id])
        # check if something is out of stock
        if stock < counts[item_id]:
            items_out_of_stock_ids.append(item_id)
            items_out_of_stock_values.append(stock)

    if filtered_items != item_ids:
        updated_order = database.update_items(order_id, filtered_items)

    order_json = order_as_json(updated_order)

    if items_out_of_stock_ids:
        order_json["not_enough_stock"] = {
            "items": items_out_of_stock_ids,
            "available_stock": items_out_of_stock_values
        }

    return order_json, 200


@app.post('/checkout/<order_id>')
def checkout(order_id):
    order_json, code = find_order(order_id)
    if code != 200:
        return order_json, code

    item_ids = order_json["items"]

    if not item_ids:
        return f"Order {order_id} does not contain any items.", 400

    if "not_enough_stock" in order_json:
        items_out_of_stock = order_json["not_enough_stock"]["items"]
        return f"Items: {items_out_of_stock} do not have enough stock available.", 400

    req_id = coordinator.checkout(order_id, item_ids, order_json["user_id"], order_json["total_cost"])

    if coordinator.wait_result(req_id):
        order_json["paid"] = True
        database.update_payment_status(order_id, True)
        return f"Success. Order {order_id} was placed.", 200
    else:
        return f"Checkout for {order_id} failed.", 400
