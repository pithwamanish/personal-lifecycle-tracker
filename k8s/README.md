# Local Kubernetes Deployment with Kind

This directory contains declarative Kubernetes manifests for deploying the **Personal Lifecycle Tracker** stack to a local Kubernetes cluster using [Kind (Kubernetes in Docker)](https://kind.sigs.k8s.io/), covering the requirements of **Homework 3 (Containerize and Deploy)**.

---

## 1. Kubernetes Architecture & Components

- **Database**: PostgreSQL 16 containerized deployment backed by a 1Gi `PersistentVolumeClaim` (`postgres-pvc`) on port 5432 with `pg_isready` health probes.
- **Backend Service**: FastAPI backend (`personal-lifecycle-backend:latest`) configured with container probes targeting `/health` on port 8000.
- **Frontend / Ingress Gateway**: Caddy 2 reverse proxy serving the static React 19 SPA and reverse proxying API traffic, exposed via `NodePort 30088`.
- **Kustomize Composition**: Managed declaratively through [`k8s/kustomization.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/k8s/kustomization.yaml).

---

## 2. Step-by-Step Deployment Instructions

### Step 1: Create a Local Kind Cluster
```bash
# Using Makefile
make kind-up

# Or directly with Kind
kind create cluster --name lifecycle-cluster
```

### Step 2: Build & Load Container Images
Build images and load them into the Kind control-plane node without pushing to a remote registry:
```bash
# Build images
docker build -t personal-lifecycle-backend:latest backend/
docker build -t personal-lifecycle-frontend:latest -f frontend/Dockerfile --target prod frontend/

# Load into Kind cluster
kind load docker-image personal-lifecycle-backend:latest --name lifecycle-cluster
kind load docker-image personal-lifecycle-frontend:latest --name lifecycle-cluster
```

### Step 3: Apply Kubernetes Manifests
```bash
# Using Makefile
make kind-deploy

# Or directly with kubectl
kubectl apply -k k8s/
```

### Step 4: Verify Pod Readiness & Rollout
```bash
# Check rollout status
kubectl rollout status deployment/lifecycle-postgres
kubectl rollout status deployment/lifecycle-backend
kubectl rollout status deployment/lifecycle-frontend

# Inspect running pods
kubectl get pods -o wide
```

### Step 5: Port-Forward & Validate Health
```bash
# Port-forward frontend service
kubectl port-forward svc/lifecycle-frontend 8088:80 &

# Verify live healthcheck
curl -f http://localhost:8088/health
```

### Step 6: Teardown Kind Cluster
```bash
make kind-down
# Or: kind delete cluster --name lifecycle-cluster
```
