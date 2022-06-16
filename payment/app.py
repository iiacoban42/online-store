import threading

from flask import Flask
import hashlib
from psycopg2 import ProgrammingError, IntegrityError

from database import *
import communication
import json

import os

app = Flask("payment-service")
database = attempt_connect()
communicator = communication.try_connect()

threading.Thread(target=lambda: communicator.start_listening()).start()

BACKUP_FILE = os.getcwd() + "/user_id.json"

with open(BACKUP_FILE, "r", encoding="utf8") as file:
    USER_ID = json.load(file)


def increment_id():
    USER_ID["user_id"] += 1
    with open(BACKUP_FILE, "w", encoding="utf8") as file:
        json.dump(USER_ID, file)


def get_shard(user_id):
    hashed = hashlib.shake_256(user_id.encode())
    # Get 6 character order_id hash
    shortened = hashed.digest(6)
    # use the order_id to get a node key
    node = database.get_node(shortened)
    return node


@app.post('/create_user')
def create_user():
    user_id = USER_ID["user_id"]
    node = get_shard(user_id)

    new_user_id = database.create_user(user_id, node)
    increment_id()
    return {
               "user_id": new_user_id
           }, 200


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    node = get_shard(user_id)
    user = database.find_user(user_id, node)
    if user is None:
        return "Not found.", 404
    return {
               "user_id": user.user_id,
               "credit": user.credit,
           }, 200


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: float):
    node = get_shard(user_id)
    res = database.add_credit(user_id, amount, node)
    if res is None:
        return f"User {user_id} was not found.", 400

    return f"Success. Added {amount} credits to user: {user_id}.", 200


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: float):
    try:
        node = get_shard(user_id)
        res = database.remove_credit(user_id, amount, node)
        if res is None:
            return f"User with id: {user_id} not found", 400
    except IntegrityError as e:
        print(e)
        return f"Not enough funds", 400

    database.create_payment(user_id, order_id, amount)
    return {
               "Success": True
           }, 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    node = get_shard(user_id)
    payment = database.find_payment(user_id, order_id, node)

    if payment is None:
        return f"Not found.", 404
    database.add_credit(user_id, payment.amount, node)
    return f"Payment of order {order_id} cancelled successfully.", 200


@app.get('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    node = get_shard(user_id)
    payment = database.find_payment(user_id, order_id, node)
    if payment is None:
        return "Not found.", 404
    return {
               "Paid": True if payment is not None else False
           }, 200


@app.get('/check_user/<user_id>/')
def check_user(user_id: str):
    node = get_shard(user_id)
    user = database.check_user(user_id, node)
    return {"user_exists": user}, 200
