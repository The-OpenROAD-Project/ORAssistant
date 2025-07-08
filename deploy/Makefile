.PHONY: init setup build-images deploy gke-up gke-down status clean format check

# Project configuration
PROJECT_ID ?= your-gcp-project-id
DOMAIN ?= your-domain.com
REGION ?= us-central1
CLUSTER_NAME ?= orassistant-cluster

init:
	@echo "Initializing GKE deployment..."
	@echo "Make sure you have configured:"
	@echo "  - PROJECT_ID: $(PROJECT_ID)"
	@echo "  - DOMAIN: $(DOMAIN)"
	@echo "  - REGION: $(REGION)"

# Setup GKE cluster and node pools
setup-cluster:
	@echo "Creating GKE cluster with optimized node pools..."
	gcloud container clusters create $(CLUSTER_NAME) \
		--region=$(REGION) \
		--node-locations=$(REGION)-a,$(REGION)-b,$(REGION)-c \
		--enable-network-policy \
		--enable-ip-alias \
		--enable-autoscaling \
		--enable-autorepair \
		--enable-autoupgrade \
		--maintenance-window-start=2023-01-01T09:00:00Z \
		--maintenance-window-end=2023-01-01T17:00:00Z \
		--maintenance-window-recurrence="FREQ=WEEKLY;BYDAY=SA" \
		--num-nodes=0 \
		--logging=SYSTEM,WORKLOAD \
		--monitoring=SYSTEM
	
	# Create backend node pool (n1-standard-4)
	gcloud container node-pools create backend-pool \
		--cluster=$(CLUSTER_NAME) \
		--region=$(REGION) \
		--machine-type=n1-standard-4 \
		--disk-size=50GB \
		--disk-type=pd-ssd \
		--enable-autoscaling \
		--min-nodes=1 \
		--max-nodes=3 \
		--enable-autorepair \
		--enable-autoupgrade \
		--node-taints=backend-workload=true:NoSchedule \
		--node-labels=workload-type=backend,cloud.google.com/gke-nodepool=backend-pool
	
	# Create frontend node pool (n1-standard-2)
	gcloud container node-pools create frontend-pool \
		--cluster=$(CLUSTER_NAME) \
		--region=$(REGION) \
		--machine-type=n1-standard-2 \
		--disk-size=20GB \
		--disk-type=pd-ssd \
		--enable-autoscaling \
		--min-nodes=1 \
		--max-nodes=2 \
		--enable-autorepair \
		--enable-autoupgrade \
		--node-taints=frontend-workload=true:NoSchedule \
		--node-labels=workload-type=frontend,cloud.google.com/gke-nodepool=frontend-pool

# Build and push Docker images
build-images:
	@echo "Building and pushing Docker images..."
	# Build backend image
	cd ../backend && docker build -t gcr.io/$(PROJECT_ID)/orassistant-backend:latest .
	docker push gcr.io/$(PROJECT_ID)/orassistant-backend:latest
	
	# Build frontend image  
	cd ../frontend/nextjs-frontend && docker build -t gcr.io/$(PROJECT_ID)/orassistant-frontend:latest .
	docker push gcr.io/$(PROJECT_ID)/orassistant-frontend:latest

# Setup domain and static IP
setup-domain:
	@echo "Setting up domain and SSL configuration..."
	./domain-setup.sh $(DOMAIN)

# Deploy application to GKE
deploy:
	@echo "Deploying ORAssistant to GKE..."
	# Update image references in deployments
	sed -i 's|gcr.io/PROJECT_ID|gcr.io/$(PROJECT_ID)|g' backend-deployment.yaml
	sed -i 's|gcr.io/PROJECT_ID|gcr.io/$(PROJECT_ID)|g' frontend-deployment.yaml
	
	# Apply all manifests in order
	kubectl apply -f namespace.yaml
	kubectl apply -f configmap.yaml
	kubectl apply -f secrets.yaml
	kubectl apply -f persistent-volume.yaml
	kubectl apply -f ssl-policy.yaml
	kubectl apply -f services.yaml
	kubectl apply -f backend-deployment.yaml
	kubectl apply -f frontend-deployment.yaml
	kubectl apply -f load-balancer.yaml
	kubectl apply -f hpa.yaml
	kubectl apply -f ingress.yaml
	kubectl apply -f certificate-management.yaml

# Complete GKE setup (cluster + deploy)
gke-up: setup-cluster build-images setup-domain deploy
	@echo "GKE deployment completed!"
	@echo "Waiting for services to be ready..."
	@kubectl wait --for=condition=Ready pod -l app=backend -n orassistant --timeout=300s
	@kubectl wait --for=condition=Ready pod -l app=frontend -n orassistant --timeout=300s
	@make status

# Deploy only (assumes cluster exists)
deploy-only: build-images deploy
	@echo "Application deployed to existing cluster"
	@make status

# Remove all resources
gke-down:
	@echo "Removing ORAssistant from GKE..."
	@kubectl delete -f . --ignore-not-found=true
	@kubectl delete namespace orassistant --ignore-not-found=true

# Delete entire cluster
delete-cluster:
	@echo "Deleting GKE cluster..."
	@gcloud container clusters delete $(CLUSTER_NAME) --region=$(REGION) --quiet

# Check deployment status
status:
	@echo "=== ORAssistant GKE Deployment Status ==="
	@echo ""
	@echo "Namespace:"
	@kubectl get namespace orassistant 2>/dev/null || echo "Namespace not found"
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n orassistant -o wide
	@echo ""
	@echo "Services:"
	@kubectl get services -n orassistant
	@echo ""
	@echo "Ingress:"
	@kubectl get ingress -n orassistant
	@echo ""
	@echo "HPA Status:"
	@kubectl get hpa -n orassistant
	@echo ""
	@echo "SSL Certificates:"
	@kubectl get managedcertificate -n orassistant
	@echo ""
	@echo "Recent Events:"
	@kubectl get events -n orassistant --sort-by=.metadata.creationTimestamp | tail -10

# Detailed status with logs
debug:
	@echo "=== Debug Information ==="
	@echo "Backend pods:"
	@kubectl describe pods -l app=backend -n orassistant
	@echo ""
	@echo "Frontend pods:"
	@kubectl describe pods -l app=frontend -n orassistant
	@echo ""
	@echo "Backend logs:"
	@kubectl logs -l app=backend -n orassistant --tail=50
	@echo ""
	@echo "Frontend logs:"
	@kubectl logs -l app=frontend -n orassistant --tail=50

# Scale application
scale-up:
	@echo "Scaling up application..."
	@kubectl scale deployment backend-deployment --replicas=3 -n orassistant
	@kubectl scale deployment frontend-deployment --replicas=2 -n orassistant

scale-down:
	@echo "Scaling down application..."
	@kubectl scale deployment backend-deployment --replicas=1 -n orassistant
	@kubectl scale deployment frontend-deployment --replicas=1 -n orassistant

# Security and monitoring
apply-security:
	@echo "Applying security policies..."
	@kubectl apply -f network-policies.yaml

# Clean up resources
clean:
	@echo "Cleaning up local files..."
	@docker system prune -f
	@gcloud container images list-tags gcr.io/$(PROJECT_ID)/orassistant-backend --filter='-tags:*' --format='value(digest)' --limit=10 | xargs -I {} gcloud container images delete gcr.io/$(PROJECT_ID)/orassistant-backend@{} --quiet
	@gcloud container images list-tags gcr.io/$(PROJECT_ID)/orassistant-frontend --filter='-tags:*' --format='value(digest)' --limit=10 | xargs -I {} gcloud container images delete gcr.io/$(PROJECT_ID)/orassistant-frontend@{} --quiet

# Development helpers
logs-backend:
	@kubectl logs -f deployment/backend-deployment -n orassistant

logs-frontend:
	@kubectl logs -f deployment/frontend-deployment -n orassistant

shell-backend:
	@kubectl exec -it deployment/backend-deployment -n orassistant -- /bin/bash

shell-frontend:
	@kubectl exec -it deployment/frontend-deployment -n orassistant -- /bin/sh

# Legacy support (for compatibility)
convert:
	@echo "Note: kompose conversion replaced with optimized Kubernetes manifests"
	@echo "Use 'make deploy' instead"

format:
	@echo "Formatting Kubernetes manifests..."
	@which kubectl >/dev/null && kubectl apply --dry-run=client -f . || echo "kubectl not available for validation"

check:
	@echo "Checking Kubernetes manifests..."
	@kubectl apply --dry-run=client -f .
