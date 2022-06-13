import threading

from flask import Flask
from psycopg2 import ProgrammingError, IntegrityError

from database import *
import communication

app = Flask("payment-service")
database = attempt_connect()
communicator = communication.try_connect()

threading.Thread(target=lambda: communicator.start_listening()).start()


@app.post('/create_user')
def create_user():
    new_user_id = database.create_user()
    return {
               "user_id": new_user_id
           }, 200


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = database.find_user(user_id)
    if user is None:
        return "Not found.", 404
    return {
               "user_id": user.user_id,
               "credit": user.credit,
           }, 200


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: float):
    database.add_credit(user_id, amount)
    return f"Added {amount} credits to user {user_id}.", 200


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: float):
    try:
        database.remove_credit(user_id, amount)
    except ProgrammingError as e:
        print(e)
        return f"User with id: {user_id} not found", 400
    except IntegrityError as e:
        print(e)
        return f"Not enough funds", 400

    new_payment = database.create_payment(user_id, order_id, amount)
    return {
        "Success": True
    }, 200


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    payment = database.find_payment(user_id, order_id)
    if payment is None:
        return f"Not found.", 404
    database.add_credit(user_id, payment.amount)
    return f"Payment of order {order_id} cancelled successfully.", 200


@app.get('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    payment = database.find_payment(user_id, order_id)
    if payment is None:
        return "Not found.", 404
    return {
               "Paid": True if payment is not None else False
           }, 200


@app.get('/check_user/<user_id>/')
def check_user(user_id: str):
    user = database.check_user(user_id)
    return {
               "user_exists": user
           }, 200
