.PHONY: init

init:
	@echo "Initializing project..."

format:
	@echo "Formatting code..."

check:
	@echo "Checking code..."

convert:
	@echo "Converting docker-compose to kubernetes..."
	@kompose convert -f ../docker-compose.yml

gke-up:
	@echo "Deploying to kubernetes..."
	@kubectl apply -f .

gke-down:
	@echo "Undeploying from kubernetes..."
	@kubectl delete -f .

status:
	@echo "Checking status of kubernetes deployment..."
	@kubectl get pods -o json
	@kubectl get services -o json
