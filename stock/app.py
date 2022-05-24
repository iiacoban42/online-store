import threading
from database import *
from flask import Flask
import redis


app = Flask("stock-service")

db = attempt_connect()


#threading.Thread(target=lambda: communicator.start_listening()).start()



@app.post('/item/create/<price>')
def create_item(price: int):
    new_item_id = db.create_user(price)
    return {
        "item_id": new_item_id
    }


@app.get('/find/<item_id>')
def find_item(item_id: str):
    item = db.find_item(item_id)
    return {
        "item_id": item.item_id,
        "price": item.price,
        "sotck": item.stock
    }


@app.post('/add/<item_id>/<amount>')
def add_stock(item_id: str, amount: int):
    db.add_stock(item_id, amount)
    return "Success"


@app.post('/subtract/<item_id>/<amount>')
def remove_stock(item_id: str, amount: int):
    item = db.find_item(item_id)
    if item.stock >= amount:
        db.remove_stock(item_id, amount)
        return {
            "Success"
        }
    return "Item not enough stock", 400
