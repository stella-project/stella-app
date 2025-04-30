# Kubernetes Deployment Guide for STELLA (Minikube Edition)

Welcome! This guide will walk you through deploying STELLA to a local Minikube Kubernetes cluster.

---

## 1. Prerequisites

Before you begin, ensure you have the following:

- Minikube installed
- `kubectl` installed
- Docker image built locally or pushed to a container registry

Test your setup:

```bash
minikube version
kubectl version --client
minikube status
```

Start Minikube:

```bash
minikube start
```

---

## 2. Using Custom or Local Docker Images with Minikube

You can use the Docker images provided in our Docker Hub registry as referenced in the Kubernetes deployment manifests. If you are using those, you can skip this step.

If you prefer to use a custom or locally built Docker image, you have two options:

Option 1: Load the local image into Minikube, if your Docker image is local.

```bash
minikube image load your-image-name:tag
```

Option 2: Push the image to a public or private container registry, then update the image reference in the Kubernetes manifests accordingly.

---

## 3. Accessing the Application

To make your services accessible, start Minikube tunnel (for LoadBalancer service type).


```bash
minikube tunnel
```

This command creates a network tunnel that allows you to access services exposed via `LoadBalancer` from your local machine.

---

## 4. Deploy the Application

Apply the Kubernetes manifests located in the `kubernetes/` directory:

```bash
kubectl apply -f .
```

---




## 5. Verify the Deployment

Check if your pods are running:

```bash
kubectl get pods
```

Check services:

```bash
kubectl get svc
```

View pod logs (optional):

```bash
kubectl logs <pod-name>
```

---

## 6. Cleaning Up

To delete all the resources:

```bash
kubectl delete -f .
```

Stop and delete Minikube (optional):

```bash
minikube stop
minikube delete
```

---

## Useful Links

- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

---

Happy Deploying on Minikube! :rocket:

