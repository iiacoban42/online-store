# Online-store
Cloud application running Stock, Order and Payment microservices, built with Python's Flask and PostgreSQL.

### Project structure

* `env`
    Folder containing the PostgreSQL env variables for the docker-compose deployment

* `helm-config`
   Helm chart values for PostgreSQL and ingress-nginx

* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.

* `order`
    Folder containing the order application logic and dockerfile.

* `payment`
    Folder containing the payment application logic and dockerfile.

* `stock`
    Folder containing the stock application logic and dockerfile.

* `test`
    Folder containing some basic correctness tests for the entire system.

### Port assignment

* `order`:5000
* `payment`:6000
* `stock`:7000

### Deployment types:

#### docker-compose (local development)

Run `docker-compose up --build` in the base folder.

***Requirements:*** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud.

To deploy the app on a minikube cluster run  `./setup-minikube.sh` (and `minikube dashboard` for monitoring). In case of an "insufficient cpu" error, pods 1-3 from `k8s/order-app.yaml`, `k8s/payment-app.yaml` and `k8s/stock-app.yaml` can be safely commented out.

The images of each service are also on dockerhub:
- bobdetest123/orderserivce:order
- bobdetest123/orderserivce:payment
- bobdetest123/orderserivce:stock


***Requirements:*** You need to have minikube (with ingress enabled) and helm installed on your machine.

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster.

***Requirements:*** You need to have access to kubectl of a k8s cluster.

