#!/bin/bash
# restarts and removes the volumes from a docker container
docker-compose down -v
docker image rm user:latest
docker image rm order:latest
docker image rm stock:latest
docker-compose up -d
echo '{"order_id": 1}' > order/order_id.json
echo '{"item_id": 1}' > stock/item_id.json
echo '{"user_id": 1}' > payment/user_id.json