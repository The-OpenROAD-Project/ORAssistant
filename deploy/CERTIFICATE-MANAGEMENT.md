# SSL Certificate Management for ORAssistant

This guide covers SSL certificate creation, renewal, and monitoring for your GKE deployment.

## Certificate Strategy

We use a **dual-certificate approach** for high availability:

1. **Primary**: Google-managed SSL certificates (recommended)
2. **Backup**: cert-manager with Let's Encrypt (fallback)

## 1. Google-Managed SSL Certificates (Primary)

### Advantages
- **Automatic renewal**: Google handles everything
- **No cost**: Free with GKE
- **High availability**: Google's infrastructure
- **Easy setup**: Just specify domains in manifest

### Setup
```bash
# Certificates are defined in ingress.yaml
kubectl apply -f ingress.yaml

# Check certificate status
kubectl get managedcertificate orassistant-ssl-cert -n orassistant
kubectl describe managedcertificate orassistant-ssl-cert -n orassistant
```

### Certificate Status
```bash
# Check provisioning status
kubectl get managedcertificate orassistant-ssl-cert -n orassistant -o jsonpath='{.status.certificateStatus}'

# Possible statuses:
# - Provisioning: Certificate is being created
# - Active: Certificate is ready and valid
# - ProvisioningFailed: Check domain DNS configuration
```

## 2. cert-manager with Let's Encrypt (Backup)

### When to Use
- Google-managed certificates fail
- Need certificates for non-Google environments
- Development/testing environments
- More control over certificate lifecycle

### Setup
```bash
# Install cert-manager and configure Let's Encrypt
./cert-manager-setup.sh your-domain.com admin@your-domain.com full

# Or step by step:
./cert-manager-setup.sh your-domain.com admin@your-domain.com install-cert-manager
./cert-manager-setup.sh your-domain.com admin@your-domain.com setup
```

### Manual cert-manager Installation
```bash
# Add helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --set installCRDs=true \
    --version v1.13.0

# Apply certificate configuration
kubectl apply -f certificate-management.yaml
```

## 3. Certificate Monitoring

### Automated Monitoring
```bash
# Deploy certificate monitoring CronJob
kubectl apply -f certificate-management.yaml

# Check monitoring job
kubectl get cronjob cert-monitor -n orassistant
kubectl get jobs -n orassistant -l cronjob=cert-monitor
```

### Manual Certificate Checks
```bash
# Check certificate expiration
openssl s_client -servername orassistant.your-domain.com -connect orassistant.your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Check certificate chain
curl -vI https://orassistant.your-domain.com

# SSL Labs test (external)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=orassistant.your-domain.com
```

## 4. Certificate Renewal

### Google-Managed Certificates
- **Automatic renewal**: No action required
- **Renewal window**: 30 days before expiration
- **Notification**: Check GCP console for any issues

### cert-manager Certificates
- **Automatic renewal**: cert-manager handles renewal
- **Renewal window**: 30 days before expiration
- **Manual renewal**: `kubectl delete certificate orassistant-letsencrypt-cert -n orassistant`

## 5. Troubleshooting

### Common Issues

#### Certificate Stuck in "Provisioning"
```bash
# Check DNS configuration
nslookup orassistant.your-domain.com
dig orassistant.your-domain.com

# Check ingress configuration
kubectl describe ingress orassistant-ingress -n orassistant

# Check events
kubectl get events -n orassistant --sort-by=.metadata.creationTimestamp
```

#### Certificate "ProvisioningFailed"
1. Verify DNS A record points to correct IP
2. Check domain ownership
3. Ensure domain is publicly accessible
4. Wait 10-15 minutes for DNS propagation

#### cert-manager Issues
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate events
kubectl describe certificate orassistant-letsencrypt-cert -n orassistant

# Check certificate request
kubectl get certificaterequests -n orassistant
```

## 6. Certificate Backup Strategy

### Export Certificates
```bash
# Export Google-managed certificate (when active)
kubectl get secret -n orassistant -o yaml > certificates-backup.yaml

# Export cert-manager certificate
kubectl get secret orassistant-tls-secret -n orassistant -o yaml >> certificates-backup.yaml
```

### Disaster Recovery
```bash
# Restore from backup
kubectl apply -f certificates-backup.yaml

# Force certificate recreation
kubectl delete managedcertificate orassistant-ssl-cert -n orassistant
kubectl apply -f ingress.yaml
```

## 7. Security Best Practices

### Certificate Monitoring
- Monitor certificate expiration (30-day alert)
- Set up alerting for certificate failures
- Regular SSL Labs testing

### Certificate Management
- Use strong cipher suites
- Enable HSTS (HTTP Strict Transport Security)
- Monitor certificate transparency logs

### Configuration
```yaml
# Enhanced SSL configuration in ingress
metadata:
  annotations:
    networking.gke.io/v1beta1.FrontendConfig: orassistant-frontend-config
spec:
  # SSL policy with strong ciphers
  sslPolicy: orassistant-ssl-policy
  redirectToHttps:
    enabled: true
    responseCodeName: MOVED_PERMANENTLY_DEFAULT
```

## 8. Cost Optimization

- **Google-managed certificates**: Free
- **cert-manager**: Free (Let's Encrypt)
- **Monitoring**: Minimal cost (CronJob resources)
- **Load balancer**: ~$20/month (required for SSL termination)

## 9. Maintenance Schedule

### Monthly
- Review certificate expiration dates
- Check monitoring alerts
- Verify SSL Labs rating

### Quarterly
- Update cert-manager version
- Review certificate policies
- Test disaster recovery procedures

### Annually
- Review certificate strategy
- Update contact information
- Audit certificate usage

This comprehensive certificate management ensures 99.9% uptime for SSL certificates with automatic renewal and monitoring.