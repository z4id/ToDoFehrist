# Minikube Setup

## Tech Stack
- Ubuntu 21.04
- Minikube v1.23.0
- Kubectl v1.22.2
- Postgres Operator v5 - CrunchData

## Minikube Setup on Ubuntu 21.04
Ref: https://minikube.sigs.k8s.io/docs/start/
```
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Exiting due to DRV_AS_ROOT: The "docker" driver should not be used with root privileges.
# https://github.com/kubernetes/minikube/issues/7903
adduser kube8
# enter password 
usermod -aG sudo kube8
su - kube8
sudo groupadd docker
sudo usermod -aG docker $USER
```

## Kubectl Setup
Ref: https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -LO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(<kubectl.sha256) kubectl" | sha256sum --check

sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client
```

## App Containerization
```
# Make sure you are in root directory 'ToDoFehrist'
docker build -t todofehrist:v1 .
docker --login  # Login for dockerhub.io
docker push todofehrist:v1
```

## Minikube Initialization
```
# switch to user which has docker permission as non root
su - kube8

# start minikube cluster locally
minikube start

# start kubernetes monitoring dashboard
minikube dashboard

# Enable Ingress
minikube addons enable ingress
```

## Create Postgres Operator Database Cluster
Ref: https://access.crunchydata.com/documentation/postgres-operator/v5/quickstart/
```
# Create Postgres Operator based DB Cluster (or skip if already created)
git clone --depth 1 "git@github.com:z4id/postgres-operator-examples.git"
cd postgres-operator-examples
kubectl apply -k kustomize/install

kubectl -n postgres-operator get pods \
  --selector=postgres-operator.crunchydata.com/control-plane=postgres-operator \
  --field-selector=status.phase=Running
  
kubectl apply -k kustomize/postgres
kubectl -n postgres-operator describe postgresclusters.postgres-operator.crunchydata.com hippo

# Connect Using a Port-Forward
# In a new terminal, create a port forward:

PG_CLUSTER_PRIMARY_POD=$(kubectl get pod -n postgres-operator -o name -l postgres-operator.crunchydata.com/cluster=hippo,postgres-operator.crunchydata.com/role=master)
kubectl -n postgres-operator port-forward "${PG_CLUSTER_PRIMARY_POD}" 5432:5432

# Return back to previous terminal session
PG_CLUSTER_USER_SECRET_NAME=hippo-pguser-hippo
PGPASSWORD=$(kubectl get secrets -n postgres-operator "${PG_CLUSTER_USER_SECRET_NAME}" -o go-template='{{.data.password | base64decode}}')
PGUSER=$(kubectl get secrets -n postgres-operator "${PG_CLUSTER_USER_SECRET_NAME}" -o go-template='{{.data.user | base64decode}}')
PGDATABASE=$(kubectl get secrets -n postgres-operator "${PG_CLUSTER_USER_SECRET_NAME}" -o go-template='{{.data.dbname | base64decode}}')

psql -h localhost -p 5432 -U hippo
# use PGPASSWORD for authentication

kubectl get pods -n postgres-operator
```

## ToDoFehristAPI Deployment - Service - Ingress
```
# Create APIs Deployment - Service and Ingress
kubectl apply -f todofehristapi-deployment.yaml
kubectl apply -f todofehristapi-service.yaml
kubectl apply -f todofehrist-ingress.yaml

# Get Minikube Cluster IP
minikube ip
# & Edit the hosts file by 
sudo nano /etc/hosts/
# and create entry for <Minikube IP> kubernetes.todofehrist.api at the end of file.
# press ctrl + x to exit and press y to save changes.
```

## Misc
```
minikube pause
minikube unpause
minikube stop
minikube delete
minikube start --v=7 --alsologtostderr
minikube tunnel

# to test a service locally in minikube
minikube service todofehristapi-service --url

kubectl get namespaces
kubectl get pods  # to get deployments
kubectl get services
kubectl get ingress

# forward port from a pod
kubectl -n default port-forward "<POD_NAME>" 8000:8000
```