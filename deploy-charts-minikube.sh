#!/usr/bin/env bash

helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install -f helm-config/postgres-helm-values.yaml order-db-0 bitnami/postgresql
helm install -f helm-config/postgres-helm-values.yaml order-db-1 bitnami/postgresql
helm install -f helm-config/postgres-helm-values.yaml order-db-2 bitnami/postgresql
helm install -f helm-config/postgres-helm-values.yaml stock-db-0 bitnami/postgresql
helm install -f helm-config/postgres-helm-values.yaml payment-db-0 bitnami/postgresql

helm install kafka bitnami/kafka