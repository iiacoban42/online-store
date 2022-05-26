FROM python:3.10-slim

WORKDIR /home/flask-app

COPY ./stock/requirements.txt .

RUN pip install -r requirements.txt

COPY ./stock .

EXPOSE 5002