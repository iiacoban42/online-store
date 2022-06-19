#!/bin/bash

minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
kubectl delete -A ValidatingWebhookConfiguration ingress-nginx-admission
kubectl apply -f ./k8s
kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller 8080:80
