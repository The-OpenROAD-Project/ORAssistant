# DNS Configuration Guide for ORAssistant

This guide explains how to connect your GKE deployment to a public domain.

## Prerequisites

- A registered domain name (e.g., `mycompany.com`)
- Access to your domain's DNS settings
- GKE cluster deployed with the provided manifests

## Step 1: Reserve Static IP

```bash
# Navigate to deploy directory
cd deploy

# Reserve a global static IP address
gcloud compute addresses create orassistant-ip --global

# Get the IP address (save this for DNS configuration)
gcloud compute addresses describe orassistant-ip --global --format="value(address)"
```

## Step 2: Configure DNS Records

In your domain registrar or DNS provider (Cloudflare, Route53, etc.), create:

### A Record
- **Name**: `orassistant` (or your preferred subdomain)
- **Type**: `A`
- **Value**: `[Static IP from Step 1]`
- **TTL**: `300` seconds

### Optional CNAME for www
- **Name**: `www.orassistant`
- **Type**: `CNAME`
- **Value**: `orassistant.your-domain.com`
- **TTL**: `300` seconds

## Step 3: Update Kubernetes Manifests

### Option A: Use the automated script
```bash
# Run the domain setup script
./domain-setup.sh your-domain.com
```

### Option B: Manual update
Replace `your-domain.com` in these files:
- `ingress.yaml` (lines 15, 36)
- Update the ManagedCertificate domains

## Step 4: Deploy the Application

```bash
# Deploy all manifests
make gke-up

# Or deploy manually
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f persistent-volume.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f services.yaml
kubectl apply -f load-balancer.yaml
kubectl apply -f hpa.yaml
kubectl apply -f ingress.yaml
```

## Step 5: Wait for SSL Certificate

The Google-managed SSL certificate will provision automatically:

```bash
# Check certificate status (takes 5-10 minutes)
kubectl get managedcertificate orassistant-ssl-cert -n orassistant

# Status should show 'Active' when ready
kubectl describe managedcertificate orassistant-ssl-cert -n orassistant
```

## Step 6: Verify Deployment

```bash
# Check all resources
kubectl get all -n orassistant

# Check ingress external IP
kubectl get ingress orassistant-ingress -n orassistant

# Test the application
curl -I https://orassistant.your-domain.com
```

## Troubleshooting

### DNS Not Resolving
```bash
# Check DNS propagation
nslookup orassistant.your-domain.com
dig orassistant.your-domain.com
```

### SSL Certificate Issues
```bash
# Check certificate status
kubectl describe managedcertificate orassistant-ssl-cert -n orassistant

# Common issues:
# - DNS not propagated (wait 10-15 minutes)
# - Domain mismatch in ingress.yaml
# - Certificate quota exceeded
```

### Backend Connection Issues
```bash
# Check backend service
kubectl get svc backend-internal-lb -n orassistant

# Check backend pods
kubectl get pods -n orassistant -l app=backend
```

## Cost Optimization

- The static IP costs ~$0.75/month when in use
- Managed SSL certificates are free
- Internal load balancer reduces data transfer costs

## Security Considerations

- Backend services are only accessible internally
- SSL termination at the load balancer
- Network policies can be added for additional security

## Example Final URLs

- **Main Application**: `https://orassistant.your-domain.com`
- **API Endpoints**: `https://orassistant.your-domain.com/api/*`
- **Health Check**: `https://orassistant.your-domain.com/api/healthcheck`

Replace `your-domain.com` with your actual domain name.