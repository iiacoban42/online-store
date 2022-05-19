from flask import Flask
from database import *

app = Flask("order-service")
database = attempt_connect()

@app.post('/create/<user_id>')
def create_order(user_id):
    pass


@app.delete('/remove/<order_id>')
def remove_order(order_id):
    pass


@app.post('/addItem/<order_id>/<item_id>')
def add_item(order_id, item_id):
    pass


@app.delete('/removeItem/<order_id>/<item_id>')
def remove_item(order_id, item_id):
    pass


@app.get('/find/<order_id>')
def find_order(order_id):
    pass


@app.post('/checkout/<order_id>')
def checkout(order_id):
    pass
