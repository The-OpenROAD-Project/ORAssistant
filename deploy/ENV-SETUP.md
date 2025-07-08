# Environment Configuration Guide

This guide explains how to configure all the necessary secrets and variables for your ORAssistant GKE deployment.

## 🔧 Quick Setup

### Automated Setup (Recommended)
```bash
cd deploy
./env-setup.sh
```

The script will:
- Prompt for required values
- Generate random secrets automatically
- Base64 encode all secrets
- Create a complete .env file

### Manual Setup
```bash
# Copy template and edit
cp .env.template .env
# Edit .env with your values
```

## 📋 Required Configuration

### 1. **Project Information**
```bash
PROJECT_ID=your-gcp-project-id        # GCP Project ID
DOMAIN=your-domain.com                 # Your domain name
REGION=us-central1                     # GCP region
```

### 2. **Critical Secrets** (Base64 encoded)
```bash
# Required for functionality
OPENAI_API_KEY=<base64-encoded-key>    # OpenAI API key
GOOGLE_API_KEY=<base64-encoded-key>    # Google AI/Vertex AI key
HUGGINGFACE_TOKEN=<base64-encoded-key> # HuggingFace token

# Database connection
MONGODB_URI=<base64-encoded-uri>       # MongoDB connection string

# Application security (auto-generated)
JWT_SECRET_KEY=<base64-encoded-secret> # JWT signing key
SESSION_SECRET=<base64-encoded-secret> # Session encryption
```

### 3. **Optional Secrets**
```bash
ANTHROPIC_API_KEY=<base64-encoded-key> # Claude API (optional)
COHERE_API_KEY=<base64-encoded-key>    # Cohere API (optional)
GOOGLE_SHEETS_CREDENTIALS=<base64-json> # Google Sheets integration
```

## 🔐 Secret Encoding

### Base64 Encoding Commands
```bash
# Encode a secret
echo -n "your-secret-value" | base64

# Encode a file (for JSON credentials)
cat service-account.json | base64 -w 0

# Generate random secret
openssl rand -hex 32 | base64
```

### Example Encodings
```bash
# OpenAI API Key
echo -n "sk-proj-abcd1234..." | base64
# Output: c2stcHJvai1hYmNkMTIzNC4uLg==

# MongoDB URI
echo -n "mongodb://user:pass@cluster.mongodb.net/db" | base64
# Output: bW9uZ29kYjovL3VzZXI6cGFzc0BjbHVzdGVyLm1vbmdvZGIubmV0L2Ri

# Random JWT secret
openssl rand -hex 32 | base64
# Output: NDJhYzFkMzRmOGE3YjllM2RjOGYyZWE1...
```

## 📁 Environment Files

### `.env.template`
- Template with all available variables
- Use as reference for configuration
- Safe to commit to version control

### `.env.example`
- Example with realistic values
- Shows proper formatting
- Safe to commit to version control

### `.env.secrets-only`
- Contains only secrets/credentials
- Minimal file for security-conscious setups
- **Never commit to version control**

### `.env` (Generated)
- Your actual configuration
- Created by env-setup.sh or manually
- **Never commit to version control**

## 🔒 Security Best Practices

### 1. **Secret Management**
```bash
# Add to .gitignore immediately
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env

# Use separate environments
.env.development
.env.staging  
.env.production
```

### 2. **Secret Generation**
```bash
# Generate strong secrets
openssl rand -hex 32    # 64-character hex string
openssl rand -base64 32 # 44-character base64 string

# Check secret strength
echo "your-secret" | wc -c  # Should be >20 characters
```

### 3. **Production Recommendations**
- Use Google Secret Manager
- Implement secret rotation
- Monitor API key usage
- Set up usage alerts
- Use sealed-secrets for GitOps

## 🚀 Deployment Process

### 1. **Configure Environment**
```bash
./env-setup.sh
# or
cp .env.template .env && nano .env
```

### 2. **Validate Configuration**
```bash
# Check required secrets are set
grep -E "(OPENAI_API_KEY|PROJECT_ID|DOMAIN)" .env

# Verify base64 encoding
echo "c2stdGVzdA==" | base64 -d  # Should output: sk-test
```

### 3. **Deploy**
```bash
make gke-up
```

## 🔍 Configuration Validation

### Required Variables Checklist
- [ ] PROJECT_ID (GCP project)
- [ ] DOMAIN (your domain)
- [ ] OPENAI_API_KEY (base64 encoded)
- [ ] GOOGLE_API_KEY (base64 encoded)  
- [ ] HUGGINGFACE_TOKEN (base64 encoded)
- [ ] JWT_SECRET_KEY (auto-generated)
- [ ] SESSION_SECRET (auto-generated)

### Validation Commands
```bash
# Check if all required variables are set
required_vars="PROJECT_ID DOMAIN OPENAI_API_KEY GOOGLE_API_KEY HUGGINGFACE_TOKEN"
for var in $required_vars; do
    if grep -q "^${var}=" .env && [ "$(grep "^${var}=" .env | cut -d'=' -f2)" != "" ]; then
        echo "✓ $var is set"
    else
        echo "✗ $var is missing or empty"
    fi
done

# Test base64 decoding (shouldn't error)
OPENAI_KEY=$(grep "OPENAI_API_KEY=" .env | cut -d'=' -f2)
echo "$OPENAI_KEY" | base64 -d >/dev/null && echo "✓ Valid base64" || echo "✗ Invalid base64"
```

## 🆘 Troubleshooting

### Common Issues

#### 1. **Invalid Base64 Encoding**
```bash
# Error: invalid input
echo "your-secret" | base64        # Wrong - adds newline
echo -n "your-secret" | base64     # Correct - no newline
```

#### 2. **Missing Required Variables**
```bash
# Check what's missing
./env-setup.sh  # Re-run setup script
# or
diff .env.template .env
```

#### 3. **API Key Format Issues**
```bash
# OpenAI keys start with 'sk-'
# Google keys start with 'AIza'
# HuggingFace tokens start with 'hf_'

# Verify key format before encoding
echo -n "$OPENAI_KEY" | base64 -d  # Should start with 'sk-'
```

#### 4. **File Permission Errors**
```bash
# Fix permissions
chmod 600 .env
chown $(whoami):$(whoami) .env
```

### Debug Commands
```bash
# Check environment variables
env | grep -E "(PROJECT_ID|DOMAIN|API_KEY)"

# Validate .env file syntax
bash -n <(sed 's/^/export /' .env)

# Test secret decoding
source .env && echo $OPENAI_API_KEY | base64 -d
```

## 📚 Additional Resources

- [Google Secret Manager](https://cloud.google.com/secret-manager)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [HuggingFace Tokens](https://huggingface.co/settings/tokens)
- [Base64 Encoding](https://en.wikipedia.org/wiki/Base64)

## 🔄 Environment Updates

### Adding New Secrets
```bash
# Add to .env
echo "NEW_SECRET=$(echo -n 'new-value' | base64)" >> .env

# Update Kubernetes secret
kubectl delete secret orassistant-secrets -n orassistant
kubectl create secret generic orassistant-secrets --from-env-file=.env -n orassistant
```

### Rotating Secrets
```bash
# Generate new secret
NEW_JWT=$(openssl rand -hex 32 | base64)

# Update .env
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT/" .env

# Redeploy
make deploy
```

This comprehensive configuration ensures secure, flexible deployment across all environments.