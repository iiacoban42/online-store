#!/bin/bash

minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
kubectl apply -f ./k8s