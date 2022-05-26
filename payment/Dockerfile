FROM python:3.10-slim

WORKDIR /home/flask-app

COPY ./payment/requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

COPY ./payment .
COPY ./shared ./shared

EXPOSE 5001