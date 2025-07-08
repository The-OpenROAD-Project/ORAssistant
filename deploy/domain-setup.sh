#!/bin/bash

# Domain Setup Script for ORAssistant GKE Deployment
# Usage: ./domain-setup.sh your-domain.com

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <your-domain.com>"
    echo "Example: $0 mycompany.com"
    exit 1
fi

DOMAIN=$1
SUBDOMAIN="orassistant"
FULL_DOMAIN="${SUBDOMAIN}.${DOMAIN}"

echo "Setting up domain configuration for: $FULL_DOMAIN"

# 1. Reserve static IP
echo "Reserving static IP..."
gcloud compute addresses create orassistant-ip --global || echo "IP already exists"

# 2. Get the IP address
STATIC_IP=$(gcloud compute addresses describe orassistant-ip --global --format="value(address)")
echo "Static IP: $STATIC_IP"

# 3. Update ingress.yaml with the domain
echo "Updating ingress configuration..."
sed -i "s/orassistant\.your-domain\.com/$FULL_DOMAIN/g" ingress.yaml

# 4. Update managed certificate
echo "Updating SSL certificate configuration..."
sed -i "s/orassistant\.your-domain\.com/$FULL_DOMAIN/g" ingress.yaml

# 5. Create domain-specific configmap
cat > domain-config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: domain-config
  namespace: orassistant
data:
  DOMAIN: "$DOMAIN"
  SUBDOMAIN: "$SUBDOMAIN"
  FULL_DOMAIN: "$FULL_DOMAIN"
  STATIC_IP: "$STATIC_IP"
EOF

echo "Domain configuration completed!"
echo ""
echo "Next steps:"
echo "1. Configure DNS A record:"
echo "   Name: $SUBDOMAIN"
echo "   Type: A"
echo "   Value: $STATIC_IP"
echo ""
echo "2. Deploy the application:"
echo "   make gke-up"
echo ""
echo "3. Wait for SSL certificate (5-10 minutes):"
echo "   kubectl get managedcertificate orassistant-ssl-cert -n orassistant"
echo ""
echo "4. Test the deployment:"
echo "   curl -I https://$FULL_DOMAIN"