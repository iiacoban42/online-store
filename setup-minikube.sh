#!/bin/bash

minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
kubectl apply -f ./k8s

kubectl create deployment stock --image=stock --port=7000
kubectl expose deployment stock
kubectl create deployment payment --image=payment --port=6000
kubectl expose deployment payment
kubectl create deployment order --image=order --port=5000
kubectl expose deployment order
