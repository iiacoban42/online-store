#!/bin/bash
# restarts and removes the volumes from a docker container
docker-compose down -v
docker image rm user:latest
docker image rm order:latest
docker image rm stock:latest
docker-compose up -d