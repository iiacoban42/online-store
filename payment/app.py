from flask import Flask
from database import *

app = Flask("payment-service")
database = attempt_connect()


@app.post('/create_user')
def create_user():
    new_user_id = database.create_user()
    return {
        "user_id": new_user_id
    }


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    user = database.find_user(user_id)
    return {
        "user_id": user.user_id,
        "credit": user.credit,
    }


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    database.add_credit(user_id, amount)
    return "Success"


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    user = database.find_user(user_id)
    if user.credit >= amount:
        new_payment = database.create_payment(user_id, order_id, amount)
        database.remove_credit(user_id, amount)
        return {
            "Success": new_payment
        }
    return "User not enough credit", 400


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    payment = database.find_payment(user_id, order_id)
    if payment is None:
        return "Payment not found", 400
    database.add_credit(user_id, payment.amount)
    return "Success"


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    payment = database.find_payment(user_id, order_id)
    return {
        "Paid": True if payment is not None else False
    }
