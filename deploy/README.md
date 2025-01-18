# Deployment using Google Kubernetes Engine (GKE)

Why GKE? This is to maintain a cloud-agnostic Kubernetes solution 
which can be easily migrated to other services if needed.

## Prerequisites

0. Install `gcloud` CLI [(guide)](https://cloud.google.com/sdk/docs/install) and
`kompose` CLI for converting `docker-compose.yml` to Kubernetes manifests
[(guide)](https://kompose.io/installation/).

The `kubectl` [(guide)](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/) 
CLI is also needed for running commands against Kubernetes clusters.

Once installed, verify that these binaries are available:

```bash
kompose --version
gcloud --version
kubectl version --client
```

1. Authenticate GCP environment.

```bash
gcloud auth login
gcloud config set project _PROJECT_ID_
```

## Kubernetes configuration

The infrastructure consists of two nodes, as follows:
- Backend: n1-standard-32
- Frontend: n1-standard-16
- other components...

Refer to the Makefile for GKE deployment commands. This is specifically placed
in this folder to avoid confusion with the instructions in the root directory,
which creates a local deployment.

```bash
make convert
make gke-up
make gke-down
make status
```

## Migration Resources

1. [GKE to EKS](https://github.com/awslabs/aws-kubernetes-migration-factory)
2. [EKS to GKE](https://cloud.google.com/kubernetes-engine/multi-cloud/docs/attached/eks/how-to/migrate-cluster)
3. [AKS to GKE](https://cloud.google.com/kubernetes-engine/multi-cloud/docs/attached/aks/how-to/migrate-cluster)
4. [GKE multi-cloud](https://cloud.google.com/kubernetes-engine/multi-cloud/)
