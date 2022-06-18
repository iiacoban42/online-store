# Online-store
Cloud application running Stock, Order and Payment microservices

Basic project structure with Python's Flask and PostgreSQL.

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
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:

#### docker-compose (local development)

After coding the REST endpoint logic run `docker-compose up --build` in the base folder to test if your logic is correct
(you can use the provided tests in the `\test` folder and change them as you wish).

***Requirements:*** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

This setup is for local k8s testing to see if your k8s config works before deploying to the cloud.
First deploy your database using helm by running the `deploy-charts-minikube.sh` file (in this example the DB is PostgreSQL
but you can find any database you want in https://artifacthub.io/ and adapt the script). Then adapt the k8s configuration files in the
`\k8s` folder to mach your system and then run `kubectl apply -f .` in the k8s folder.

***Requirements:*** You need to have minikube (with ingress enabled) and helm installed on your machine.


Run the following for a first time setup (or `./setup-minikube.sh`) and run `minikube dashboard` for monitoring:
```
minikube start
minikube addons enable ingress
./deploy-charts-minikube.sh
kubectl apply -f ./k8s
```

The images of each service are also on dockerhub:
- bobdetest123/orderserivce:order
- bobdetest123/orderserivce:payment
- bobdetest123/orderserivce:stock

#### kubernetes cluster (managed k8s cluster in the cloud)

Similarly to the `minikube` deployment but run the `deploy-charts-cluster.sh` in the helm step to also install an ingress to the cluster.

***Requirements:*** You need to have access to kubectl of a k8s cluster.

