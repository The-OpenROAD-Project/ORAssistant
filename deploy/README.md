# Cost-Efficient GKE Deployment for ORAssistant

This directory contains optimized Kubernetes manifests for deploying ORAssistant on Google Kubernetes Engine (GKE) with significant cost savings and improved performance.

## 🎯 Cost Optimization Summary

- **Previous Cost**: $2000-3000/month (n1-standard-32 + n1-standard-16)
- **Optimized Cost**: $250-620/month (right-sized nodes + autoscaling)
- **Savings**: 75-90% cost reduction
- **Performance**: Better scalability and reliability

## 📋 Prerequisites

### Required Tools
```bash
# Install required CLI tools
gcloud --version        # Google Cloud CLI
kubectl version --client # Kubernetes CLI
docker --version        # Docker for building images
helm version           # Helm (for cert-manager)
```

### GCP Authentication
```bash
gcloud auth login
gcloud auth configure-docker
gcloud config set project YOUR_PROJECT_ID
```

## 🏗️ Architecture Overview

### Node Configuration
- **Backend Pool**: 1-3 × n1-standard-4 (4 vCPUs, 15GB RAM)
- **Frontend Pool**: 1-2 × n1-standard-2 (2 vCPUs, 7.5GB RAM)
- **Storage**: 10GB Regional PD for RAG dataset (shared)

### Load Balancer Strategy
- **External LB**: Public traffic → Frontend
- **Internal LB**: Frontend → Backend (private network)
- **Cost Benefit**: Reduced data transfer costs

### Security Features
- Network policies for traffic isolation
- HTTPS-only with auto SSL certificates
- Private backend services
- Resource limits and monitoring

## 🚀 Quick Start

### 1. Configure Environment
```bash
# Set your project configuration
export PROJECT_ID="your-gcp-project-id"
export DOMAIN="your-domain.com"
export REGION="us-central1"

# Or edit deploy/Makefile directly
```

### 2. Complete Deployment
```bash
cd deploy

# Full deployment (creates cluster + deploys app)
make gke-up PROJECT_ID=$PROJECT_ID DOMAIN=$DOMAIN

# Check deployment status
make status
```

### 3. Deploy to Existing Cluster
```bash
# If cluster already exists
make deploy-only PROJECT_ID=$PROJECT_ID

# Manual deployment steps
make build-images
make setup-domain  
make deploy
```

## 📁 File Structure

### Core Manifests
- `namespace.yaml` - Dedicated namespace
- `configmap.yaml` - Application configuration
- `secrets.yaml` - API keys and credentials (configure before deploy)
- `persistent-volume.yaml` - Shared storage for RAG dataset

### Application Deployments
- `backend-deployment.yaml` - FastAPI backend with resource limits
- `frontend-deployment.yaml` - Next.js frontend with optimization
- `services.yaml` - Internal service communication
- `hpa.yaml` - Horizontal Pod Autoscaling

### Networking & Security
- `load-balancer.yaml` - External/internal load balancer config
- `ingress.yaml` - HTTPS ingress with SSL termination
- `network-policies.yaml` - Security traffic policies
- `ssl-policy.yaml` - Enhanced SSL configuration

### SSL Certificate Management
- `certificate-management.yaml` - Google-managed + cert-manager SSL
- `cert-manager-setup.sh` - Automated certificate setup
- `CERTIFICATE-MANAGEMENT.md` - Complete SSL guide

### Domain Integration
- `dns-configuration.yaml` - DNS setup instructions
- `domain-setup.sh` - Automated domain configuration
- `DNS-SETUP.md` - Complete domain setup guide

## ⚙️ Configuration

### 1. Configure Secrets
```bash
# Edit secrets.yaml with your API keys (base64 encoded)
kubectl create secret generic orassistant-secrets \
  --from-literal=OPENAI_API_KEY="your-key" \
  --from-literal=GOOGLE_API_KEY="your-key" \
  --from-literal=HUGGINGFACE_TOKEN="your-token" \
  --namespace=orassistant
```

### 2. Set Up Domain
```bash
# Automated domain setup
./domain-setup.sh your-domain.com

# Manual steps in DNS-SETUP.md
```

### 3. Build and Deploy
```bash
# Build images
make build-images PROJECT_ID=$PROJECT_ID

# Deploy application
make deploy
```

## 🔍 Monitoring & Management

### Check Status
```bash
make status          # Overall deployment status
make debug           # Detailed debugging info
kubectl get all -n orassistant
```

### View Logs
```bash
make logs-backend    # Backend logs
make logs-frontend   # Frontend logs
kubectl logs -f deployment/backend-deployment -n orassistant
```

### Scaling
```bash
make scale-up        # Scale to full capacity
make scale-down      # Scale to minimum
kubectl scale deployment backend-deployment --replicas=3 -n orassistant
```

## 🛡️ Security Features

### Network Policies
```bash
make apply-security  # Apply network security policies
```

### SSL Certificates
- Google-managed SSL (automatic renewal)
- cert-manager backup (Let's Encrypt)
- Certificate monitoring and alerting

### Access Control
- Private backend services (internal LB only)
- Resource limits and quotas
- Network traffic isolation

## 💰 Cost Management

### Current Costs
- **Cluster**: $250-620/month (optimized nodes)
- **Load Balancer**: ~$20/month  
- **Storage**: ~$2/month (10GB PD)
- **SSL Certificates**: Free (Google-managed)

### Cost Optimization Features
- Horizontal Pod Autoscaling (scale pods before nodes)
- Right-sized node pools (no over-provisioning)
- Regional persistent disks (cost-efficient)
- Internal load balancer for backend traffic

### Clean Up
```bash
make gke-down        # Remove application
make delete-cluster  # Remove entire cluster
make clean          # Clean local images
```

## 🔧 Advanced Usage

### Development Helpers
```bash
make shell-backend   # Shell into backend pod
make shell-frontend  # Shell into frontend pod
kubectl exec -it deployment/backend-deployment -n orassistant -- bash
```

### Certificate Management
```bash
./cert-manager-setup.sh your-domain.com admin@your-domain.com full
kubectl get managedcertificate -n orassistant
```

### Debugging
```bash
kubectl describe pods -l app=backend -n orassistant
kubectl get events -n orassistant --sort-by=.metadata.creationTimestamp
```

## 📚 Documentation

- `CERTIFICATE-MANAGEMENT.md` - Complete SSL certificate guide
- `DNS-SETUP.md` - Domain configuration walkthrough
- `network-policies.yaml` - Security policy documentation

## 🔄 Migration Resources

1. [GKE to EKS](https://github.com/awslabs/aws-kubernetes-migration-factory)
2. [EKS to GKE](https://cloud.google.com/kubernetes-engine/multi-cloud/docs/attached/eks/how-to/migrate-cluster)
3. [AKS to GKE](https://cloud.google.com/kubernetes-engine/multi-cloud/docs/attached/aks/how-to/migrate-cluster)
4. [GKE multi-cloud](https://cloud.google.com/kubernetes-engine/multi-cloud/)

## 🆘 Troubleshooting

### Common Issues
1. **Pod stuck in Pending**: Check node capacity and resource requests
2. **SSL certificate not ready**: Wait 5-10 minutes, check DNS propagation
3. **Backend connection errors**: Verify internal load balancer configuration
4. **Out of resources**: Check HPA and cluster autoscaler settings

### Support
```bash
# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top nodes
kubectl top pods -n orassistant
```

This deployment provides production-ready, cost-optimized ORAssistant hosting with enterprise security and scalability features.
