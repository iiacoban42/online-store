from flask import Flask
from database import *

app = Flask("order-service")
database = attempt_connect()

@app.get('/hello')
def hello_world():
    return "<p>Hello, World!</p>"

@app.post('/create/<user_id>')
def create_order(user_id):
    new_order_id = database.create_order(user_id)
    return {
        "order_id": new_order_id
    }


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    database.remove_order(order_id)


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    pass


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    pass


@app.get('/find/<order_id>')
def find_order(order_id):
    order = database.find_order(order_id)

    return {
        "order_id": order[0],
        "paid": order[1],
        "items": order[2],
        "user_id": order[3],
        "total_cost": order[4]
    }


@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass