# Kubernetes Deployment Guide (Minikube)

This document describes the step-by-step process to run the project on a local Kubernetes cluster using **Minikube**.

---

## Prerequisites

Make sure the following tools are installed on your system:

- Docker
- Minikube
- kubectl

Verify installations:

```bash
docker --version
minikube version
kubectl version --client
```

### Step 1: Build Service Images

First, build Docker images for all services.

```bash
docker build -t users-service:latest ./services/users
docker build -t orders-service:latest ./services/orders
docker build -t products-service:latest ./services/products
docker build -t products-service:latest ./services/notifications
docker build -t products-service:latest ./gateway
```

### Step 2: Start Minikube

Start the Minikube cluster:

```bash
minikube start
```

(Optional) Use Docker inside Minikube:

```bash
eval $(minikube docker-env)
```

### Step 3: Load Images into Minikube

```bash
minikube image load users-service:latest
minikube image load orders-service:latest
minikube image load products-service:latest
```

Verify images:

```bash
minikube image ls
```

## Step 4: Apply Kubernetes YAML Files (In Order)

Apply the Kubernetes manifests in the correct order:

#### 1. Keycloak service

```bash
kubectl apply -f k8s/keycloak/postgres.yml
kubectl apply -f k8s/keycloak/deployment.yml
```

#### 2. Kafka

```bash
kubectl apply -f k8s/kafka.yml
```

#### 3. Users Service

```bash
kubectl apply -f k8s/users/redis.yml
kubectl apply -f k8s/users/citus-coordinator.yml
kubectl apply -f k8s/users/citus-workers.yml
kubectl apply -f k8s/users/deployment.yml
```

#### 4. Products Service

```bash
kubectl apply -f k8s/products/redis.yml
kubectl apply -f k8s/products/postgres.yml
kubectl apply -f k8s/products/deployment.yml
```

#### 4. Orders Service

```bash
kubectl apply -f k8s/orders/mongo.yml
kubectl apply -f k8s/orders/deployment.yml
```

#### 5. Notifications Service

```bash
kubectl apply -f k8s/notifications/redis.yml
kubectl apply -f k8s/notifications/deployment.yml
```

#### 6. API Gateway

```bash
kubectl apply -f k8s/gateway/deployment.yml
```

#### 6. Ingress

```bash
kubectl apply -f k8s/ingress.yml
```

#### 8. Independent services(Optional)

```bash
kubectl apply -f k8s/mongo-express.yml
kubectl apply -f k8s/pgadmin.yml
```

## Verify Deployment

```bash
kubectl get pods
kubectl get services
```


## Cleanup

Delete all resources in namespace:

```bash
kubectl delete all --all	
```

To stop or delete Minikube:

```bash
minikube stop
minikube delete
```