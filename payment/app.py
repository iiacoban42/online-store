import os
import atexit

from flask import Flask
import psycopg2


app = Flask("payment-service")

db = psycopg2.connect(host=os.environ['POSTGRES_HOST'],
                      port=int(os.environ['POSTGRES_PORT']),
                      user=os.environ['POSTGRES_USER'],
                      password=os.environ['POSTGRES_PASSWORD'],
                      database=int(os.environ['POSTGRES_DB']))


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post('/create_user')
def create_user():
    pass


@app.get('/find_user/<user_id>')
def find_user(user_id: str):
    pass


@app.post('/add_funds/<user_id>/<amount>')
def add_credit(user_id: str, amount: int):
    pass


@app.post('/pay/<user_id>/<order_id>/<amount>')
def remove_credit(user_id: str, order_id: str, amount: int):
    pass


@app.post('/cancel/<user_id>/<order_id>')
def cancel_payment(user_id: str, order_id: str):
    pass


@app.post('/status/<user_id>/<order_id>')
def payment_status(user_id: str, order_id: str):
    pass
