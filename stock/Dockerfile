FROM python:3.8-slim

WORKDIR /home/flask-app

COPY ./stock/requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2 \
    && pip install requests

COPY ./stock .
COPY ./shared ./shared

EXPOSE 5200