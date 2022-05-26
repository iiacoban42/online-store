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
    }


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = database.find_item(item_id)
    return {
        "item_id": item.item_id,
        "price": item.price,
        "stock": item.stock
    }


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    database.add_stock(item_id, amount)
    return "Success"


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    item = database.find_item(item_id)
    if item.stock >= amount:
        database.remove_stock(item_id, amount)
        return {
            "Success"
        }
    return "Item not enough stock", 400
