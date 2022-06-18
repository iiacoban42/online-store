#!/bin/bash
minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
cd k8s

#kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql \
#    --env="POSTGRES_PASSWORD=test123" --command -- psql --host order-db-0 -U postgres -d 0 -p 5101 -c "create database 0"
#
#kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql \
#    --env="POSTGRES_PASSWORD=test123" --command -- psql --host order-db-1 -U postgres -d 0 -p 5102 -c "create database 0"
#
#kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql \
#    --env="POSTGRES_PASSWORD=test123" --command -- psql --host order-db-2 -U postgres -d 0 -p 5103 -c "create database 0"
#
#kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql \
#    --env="POSTGRES_PASSWORD=test123" --command -- psql --host stock-db-0 -U postgres -d 0 -p 7101 -c "create database 0"
#
#kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql \
#    --env="POSTGRES_PASSWORD=test123" --command -- psql --host payment-db-0 -U postgres -d 0 -p 6101 -c "create database 0"

kubectl apply -f .
cd ..
eval $(minikube -p minikube docker-env)