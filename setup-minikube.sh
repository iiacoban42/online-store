#!/bin/bash
minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
cd k8s
kubectl apply -f .
cd ..
eval $(minikube -p minikube docker-env)