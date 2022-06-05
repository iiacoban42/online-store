import threading

from flask import Flask
from database import *
import communication


app = Flask("stock-service")

database = attempt_connect()

communicator = communication.try_connect()
threading.Thread(target=lambda: communicator.start_listening()).start()


@app.post('/item/create/<price>')
def create_item(price: int):
    new_item_id = database.create_item(price)
    return {
        "item_id": new_item_id
    }, 200


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = database.find_item(item_id)
    if item is None:
        return f"Item: {item_id} not found.", 400
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
    if database.remove_stock(item_id, amount) is None:
        return f"Cannot deduct {amount}, from {item_id}. Not enough stock, or item was not found.", 400

    return f"Success. Deducted {amount} from item: {item_id}.", 200
