import threading

from flask import Flask
from psycopg2 import ProgrammingError, IntegrityError

from database import *
import communication

app = Flask("stock-service")

database = attempt_connect()

communicator = communication.try_connect()
threading.Thread(target=lambda: communicator.start_listening()).start()


@app.post('/item/create/<price>')
def create_item(price: int):
    try:
        new_item_id = database.create_item(price)
    except IntegrityError as e:
        print(e)
        return f"Price cannot be negative", 400
    return {
               "item_id": new_item_id
           }, 200


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = database.find_item(item_id)
    if item is None:
        return f"Not found.", 400
    return {
               "item_id": item[0],
               "price": item[1],
               "stock": item[2]
           }, 200


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    if database.add_stock(item_id, amount) is None:
        return f"Item {item_id} was not found.", 400

    return f"Success. Added {amount} to item: {item_id}.", 200


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    try:
        res = database.remove_stock(item_id, amount)
        if res is None:
            return f"Item with id: {item_id} not found", 400
    except IntegrityError as e:
        print(e)
        return f"Not enough stock", 400

    return f"Success. Deducted {amount} from item: {item_id}.", 200


@app.get('/calculate_cost/<item_ids>')
def calculate_cost(item_ids: str):
    items = item_ids.split(",")
    items = list(map(str, items))
    cost, available_stock = database.calculate_cost(items)
    if cost is None:
        return f"Items: {item_ids} not found.", 400
    return {
               "cost": cost,
               "available_stock": available_stock
           }, 200
