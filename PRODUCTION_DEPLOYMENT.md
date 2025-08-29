# Production Deployment Guide for Marimo with AI Agent

This guide covers deploying Marimo with the enhanced AI Agent capabilities in production environments.

## 🚀 Quick Start Production Setup

### 1. Environment Setup

Create a production `.env` file:

```bash
# Production Configuration
NODE_ENV=production
MARIMO_ENV=production

# Google Gemini (Primary - Recommended for cost-effectiveness)
GOOGLE_AI_API_KEY=your-production-api-key-here

# Agent Configuration
MARIMO_AGENT_DEFAULT_MODEL=google/gemini-2.0-flash-exp
MARIMO_AGENT_AUTO_EXECUTE=false
MARIMO_AGENT_REQUIRE_APPROVAL=true
MARIMO_AGENT_MAX_STEPS=10
MARIMO_AGENT_STREAM_RESPONSES=true
MARIMO_AGENT_SAFETY_MODE=strict  # Use strict for production
MARIMO_AGENT_LOG_LEVEL=WARNING

# Server Configuration
MARIMO_HOST=0.0.0.0
MARIMO_PORT=8080
MARIMO_BASE_URL=/
MARIMO_ALLOW_ORIGINS=https://yourdomain.com
MARIMO_TOKEN=true
MARIMO_TOKEN_PASSWORD=your-secure-token-here

# Resource Limits
MARIMO_MAX_MEMORY_MB=4096
MARIMO_TIMEOUT_SECONDS=300
MARIMO_MAX_CONCURRENT_SESSIONS=50
```

### 2. Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY pnpm-lock.yaml ./

# Install pnpm and frontend dependencies
RUN npm install -g pnpm && pnpm install

# Copy Python requirements and install
COPY pyproject.toml ./
COPY marimo/ ./marimo/
RUN pip install -e ".[recommended]"

# Install additional AI dependencies
RUN pip install google-genai openai anthropic groq

# Copy frontend source
COPY frontend/ ./frontend/

# Build frontend
RUN pnpm run build

# Copy remaining files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 marimo && chown -R marimo:marimo /app
USER marimo

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start server
CMD ["marimo", "edit", "--host", "0.0.0.0", "--port", "8080", "--no-browser"]
```

### 3. Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  marimo:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - MARIMO_ENV=production
    env_file:
      - .env.production
    volumes:
      - ./notebooks:/app/notebooks
      - marimo-data:/app/data
    restart: unless-stopped
    networks:
      - marimo-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - marimo
    networks:
      - marimo-network
    restart: unless-stopped

volumes:
  marimo-data:

networks:
  marimo-network:
    driver: bridge
```

### 4. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream marimo {
        server marimo:8080;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # WebSocket support for agent
        location /api/agent/stream {
            proxy_pass http://marimo;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout settings for long-running connections
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }

        location / {
            proxy_pass http://marimo;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Increase buffer sizes for large notebooks
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }
    }
}
```

## 🔒 Security Best Practices

### 1. API Key Management

Use a secrets management service:

```python
# secrets_manager.py
import os
from typing import Optional
import boto3  # For AWS Secrets Manager
# or
from azure.keyvault.secrets import SecretClient  # For Azure Key Vault
# or
from google.cloud import secretmanager  # For Google Secret Manager

class SecretManager:
    @staticmethod
    def get_api_key(provider: str) -> Optional[str]:
        # Try environment variable first
        key = os.getenv(f"{provider.upper()}_API_KEY")
        if key:
            return key
        
        # Then try secrets manager
        # Example for AWS Secrets Manager:
        try:
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(
                SecretId=f'marimo/{provider}/api-key'
            )
            return response['SecretString']
        except Exception:
            return None
```

### 2. Rate Limiting

Add rate limiting middleware:

```python
# rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, user_id: str) -> bool:
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.requests_per_minute:
            return False
        
        self.requests[user_id].append(now)
        return True
```

### 3. Input Sanitization

Add input validation for agent requests:

```python
# validators.py
import re
from typing import Optional

class InputValidator:
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'__import__',
        r'exec\s*\(',
        r'eval\s*\(',
        r'os\.system',
        r'subprocess\.',
        r'open\s*\(.*/etc/',
    ]
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> tuple[bool, Optional[str]]:
        """Validate user prompt for safety."""
        # Check length
        if len(prompt) > 10000:
            return False, "Prompt too long (max 10000 characters)"
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False, f"Potentially dangerous pattern detected"
        
        return True, None
```

## 🎯 Kubernetes Deployment

### Kubernetes Manifests

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marimo-agent
  labels:
    app: marimo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: marimo
  template:
    metadata:
      labels:
        app: marimo
    spec:
      containers:
      - name: marimo
        image: your-registry/marimo-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: marimo-secrets
              key: google-api-key
        - name: MARIMO_AGENT_DEFAULT_MODEL
          value: "google/gemini-2.0-flash-exp"
        - name: MARIMO_AGENT_SAFETY_MODE
          value: "strict"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: marimo-service
spec:
  selector:
    app: marimo
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

## 📊 Monitoring & Observability

### 1. Prometheus Metrics

Add metrics endpoint:

```python
# metrics.py
from prometheus_client import Counter, Histogram, generate_latest
import time

# Define metrics
agent_requests = Counter('marimo_agent_requests_total', 
                         'Total agent requests', 
                         ['model', 'status'])
agent_latency = Histogram('marimo_agent_request_duration_seconds',
                          'Agent request latency',
                          ['model'])

# Track metrics
def track_agent_request(model: str, status: str, duration: float):
    agent_requests.labels(model=model, status=status).inc()
    agent_latency.labels(model=model).observe(duration)
```

### 2. Logging Configuration

Configure structured logging:

```python
# logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'timestamp': '@timestamp'}
    )
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
        npm install -g pnpm
        pnpm install
    
    - name: Run tests
      run: |
        pytest tests/
        pnpm test
    
    - name: Build frontend
      run: pnpm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      env:
        DOCKER_REGISTRY: ${{ secrets.DOCKER_REGISTRY }}
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      run: |
        echo $DOCKER_PASSWORD | docker login $DOCKER_REGISTRY -u $DOCKER_USERNAME --password-stdin
        docker build -t $DOCKER_REGISTRY/marimo-agent:latest .
        docker push $DOCKER_REGISTRY/marimo-agent:latest
    
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl rollout restart deployment/marimo-agent
        kubectl rollout status deployment/marimo-agent
```

## 🏷️ Cost Optimization

### Google Gemini Pricing (Dec 2024)

| Model | Input | Output | Free Tier |
|-------|-------|--------|-----------|
| Gemini 2.0 Flash | $0.075/1M tokens | $0.30/1M tokens | 15 RPM, 1M TPM |
| Gemini 1.5 Flash | $0.075/1M tokens | $0.30/1M tokens | 15 RPM, 1M TPM |
| Gemini 1.5 Flash-8B | $0.0375/1M tokens | $0.15/1M tokens | 15 RPM, 4M TPM |
| Gemini 1.5 Pro | $1.25/1M tokens | $5.00/1M tokens | 2 RPM, 32K TPM |

### Cost Optimization Tips

1. **Use Gemini Flash models** for most tasks (80% cost reduction vs Pro)
2. **Enable caching** for repeated queries
3. **Implement request batching** where possible
4. **Use Flash-8B** for simple tasks
5. **Monitor token usage** with metrics

## 🔧 Troubleshooting

### Common Production Issues

| Issue | Solution |
|-------|----------|
| WebSocket disconnections | Increase proxy timeout settings |
| High memory usage | Limit concurrent sessions, enable swap |
| Slow responses | Use Gemini Flash models, enable caching |
| API rate limits | Implement request queuing, use multiple API keys |
| SSL certificate issues | Use Let's Encrypt with auto-renewal |

### Health Check Endpoints

Add health check endpoints:

```python
# health.py
from starlette.responses import JSONResponse

async def health_check(request):
    """Basic health check."""
    return JSONResponse({"status": "healthy"})

async def ready_check(request):
    """Readiness check including dependencies."""
    checks = {
        "database": check_database(),
        "agent": check_agent_connection(),
        "storage": check_storage(),
    }
    
    if all(checks.values()):
        return JSONResponse({"status": "ready", "checks": checks})
    else:
        return JSONResponse(
            {"status": "not ready", "checks": checks},
            status_code=503
        )
```

## 📝 Production Checklist

- [ ] API keys stored securely (not in code)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] Safety mode set to "strict"
- [ ] Logging configured with appropriate levels
- [ ] Monitoring and alerting set up
- [ ] Backup and recovery plan in place
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Documentation updated
- [ ] Runbook created for incidents

## 🚀 Launch Command

```bash
# Production launch with all optimizations
docker-compose -f docker-compose.yml up -d

# Or with Kubernetes
kubectl apply -f k8s-deployment.yaml

# Monitor logs
docker-compose logs -f marimo
# or
kubectl logs -f deployment/marimo-agent
```

---

**Your production Marimo with AI Agent is ready to deploy! 🎉**