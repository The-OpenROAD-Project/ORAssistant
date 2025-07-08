#!/bin/bash

# Certificate Management Setup Script for ORAssistant
# This script sets up both Google-managed certificates and cert-manager as backup

set -e

DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"admin@${DOMAIN}"}
NAMESPACE="orassistant"

echo "Setting up certificate management for domain: $DOMAIN"
echo "Admin email: $EMAIL"

# Function to install cert-manager
install_cert_manager() {
    echo "Installing cert-manager..."
    
    # Add cert-manager helm repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager
    helm install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --set installCRDs=true \
        --version v1.13.0
    
    # Wait for cert-manager to be ready
    echo "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=Ready pod -l app=cert-manager -n cert-manager --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=webhook -n cert-manager --timeout=300s
    kubectl wait --for=condition=Ready pod -l app=cainjector -n cert-manager --timeout=300s
}

# Function to setup certificate management
setup_certificates() {
    echo "Setting up certificate configuration..."
    
    # Update certificate files with actual domain and email
    sed -i "s/your-domain\.com/$DOMAIN/g" certificate-management.yaml
    sed -i "s/admin@your-domain\.com/$EMAIL/g" certificate-management.yaml
    
    # Apply certificate configuration
    kubectl apply -f certificate-management.yaml
}

# Function to check certificate status
check_certificate_status() {
    echo "Checking certificate status..."
    
    # Check Google-managed certificate
    echo "Google-managed certificate status:"
    kubectl get managedcertificate orassistant-ssl-cert -n $NAMESPACE -o jsonpath='{.status.certificateStatus}' || echo "Not found"
    
    # Check cert-manager certificate (if exists)
    echo "cert-manager certificate status:"
    kubectl get certificate orassistant-letsencrypt-cert -n $NAMESPACE -o jsonpath='{.status.conditions[0].type}' || echo "Not found"
}

# Main execution
case "${3:-setup}" in
    "install-cert-manager")
        install_cert_manager
        ;;
    "setup")
        setup_certificates
        ;;
    "status")
        check_certificate_status
        ;;
    "full")
        install_cert_manager
        setup_certificates
        echo "Waiting 30 seconds for resources to be created..."
        sleep 30
        check_certificate_status
        ;;
    *)
        echo "Usage: $0 <domain> <email> [install-cert-manager|setup|status|full]"
        echo "Example: $0 mycompany.com admin@mycompany.com full"
        exit 1
        ;;
esac

echo "Certificate management setup completed!"
echo ""
echo "Next steps:"
echo "1. Wait 5-10 minutes for Google-managed certificate to provision"
echo "2. Check status: kubectl get managedcertificate orassistant-ssl-cert -n $NAMESPACE"
echo "3. Monitor certificate: kubectl logs -f deployment/cert-monitor -n $NAMESPACE"