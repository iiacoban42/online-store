import threading

from flask import Flask

import json
import hashlib

from psycopg2 import ProgrammingError, IntegrityError

from database import *
import communication

import os

app = Flask("stock-service")

database = attempt_connect()

communicator = communication.try_connect()
threading.Thread(target=lambda: communicator.start_listening()).start()

BACKUP_FILE = os.getcwd() + "/item_id.json"

with open(BACKUP_FILE, "r", encoding="utf8") as file:
    ITEM_ID = json.load(file)


def increment_id():
    ITEM_ID["item_id"] += 1
    with open(BACKUP_FILE, "w", encoding="utf8") as file:
        json.dump(ITEM_ID, file)


def get_shard(item_id):
    hashed = hashlib.shake_256(str(item_id).encode())
    # Get 6 character order_id hash
    shortened = hashed.digest(6)
    # use the order_id to get a node key
    node = database.get_node(shortened)
    return node


@app.post('/item/create/<price>')
def create_item(price: int):

    try:
        item_id = ITEM_ID["item_id"]
        node = get_shard(item_id)
        new_item_id = database.create_item(price, item_id, node)
        increment_id()
    except IntegrityError as e:
        print(e)
        return f"Price cannot be negative", 400

    return {
               "item_id": new_item_id
           }, 200


@app.get('/find/<item_id>')
def find_item(item_id: str):
    node = get_shard(item_id)
    item = database.find_item(item_id, node)
    if item is None:
        return f"Not found.", 400
    return {
               "item_id": item[0],
               "price": item[1],
               "stock": item[2]
           }, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    node = get_shard(item_id)
    if database.add_stock(item_id, amount, node) is None:
        return f"Item {item_id} was not found.", 400

    return f"Success. Added {amount} to item: {item_id}.", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):

    try:
        node = get_shard(item_id)
            if database.remove_stock(item_id, amount, node) is None:
                return f"Cannot deduct {amount}, from {item_id}. Not enough stock, or item was not found.", 400
    except IntegrityError as e:
        print(e)
        return f"Not enough stock", 400


    return f"Success. Deducted {amount} from item: {item_id}.", 200


@app.get('/calculate_cost/<item_ids>')
def calculate_cost(item_ids: str):
    items = item_ids.split(",")
    items = list(map(int, items))

    shard_and_items = {}  # {shard: items_in_shard}
    cost = 0
    available_stock = []

    for item in items:
        shard = get_shard(str(item))
        if shard not in shard_and_items:
            shard_and_items[shard] = [item]
        else:
            shard_and_items[shard].append(item)

    for shard, shard_items in shard_and_items.items():
        shard_cost, shard_available_stock = database.calculate_cost(shard_items, shard)
        cost += shard_cost
        available_stock.extend(shard_available_stock)

    if cost is None:
        return f"Items: {item_ids} not found.", 400
    return {
               "cost": cost,
               "available_stock": available_stock
           }, 200
