# 🚀 Production Deployment Guide
## Agentic Research AI

**Last Updated:** March 2026  
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Production Deployment](#production-deployment)
6. [Monitoring & Logging](#monitoring--logging)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Node.js** 18+ (for local frontend development)
- **Python** 3.11+ (for local backend development)
- **PostgreSQL** 15+ (if not using Docker)
- **Ollama** (optional, for local AI models)

### Infrastructure Requirements

**Minimum (Development):**
- 4 CPU cores
- 8 GB RAM
- 20 GB disk space

**Recommended (Production):**
- 8 CPU cores
- 16 GB RAM
- 100 GB SSD storage
- Dedicated GPU (optional, for Ollama)

---

## Quick Start (Docker)

### 1. Clone Repository
```bash
git clone https://github.com/your-org/agentic-research-ai.git
cd agentic-research-ai
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# REQUIRED: Change these values
JWT_SECRET_KEY=
POSTGRES_PASSWORD=

# OPTIONAL: Add AI API keys
OPENROUTER_API_KEY=
GEMINI_API_KEY=
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Verify Installation
```bash
# Backend health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","ai":"connected"}

# Frontend (open in browser)
open http://localhost:3000
```

### 5. Create First User
```bash
# Register via UI: http://localhost:3000/register
# Or via API:
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin User",
    "email": "admin@example.com",
    "password": "SecurePassword123!"
  }'
```

---

## Environment Configuration

### Complete `.env` Reference
```bash
# ==============================================
# APPLICATION SETTINGS
# ==============================================
APP_NAME="Agentic Research AI"
APP_MODE=production  # demo | production
DEBUG=False
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR

# ==============================================
# DATABASE
# ==============================================
POSTGRES_DB=agentic_research
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION
DATABASE_URL=postgresql+asyncpg://postgres:CHANGE_ME_IN_PRODUCTION@postgres:5432/agentic_research

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ==============================================
# AI CONFIGURATION
# ==============================================
# Ollama (Local AI - Primary)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b

# OpenRouter (Cloud AI - Fallback)
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Google Gemini (Cloud AI - Fallback)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-pro

# ==============================================
# AUTHENTICATION
# ==============================================
# Generate secure key: openssl rand -hex 32
JWT_SECRET_KEY=GENERATE_SECURE_KEY_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth (Optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# ==============================================
# CORS & SECURITY
# ==============================================
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
ALLOWED_HOSTS=your-domain.com,*.your-domain.com

# ==============================================
# FRONTEND
# ==============================================
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com

# ==============================================
# ANALYTICS CONNECTORS (Optional)
# ==============================================
POSTHOG_API_KEY=
POSTHOG_PROJECT_ID=
GA4_PROPERTY_ID=
BIGQUERY_PROJECT_ID=

# ==============================================
# MONITORING (Optional)
# ==============================================
SENTRY_DSN=
DATADOG_API_KEY=
PROMETHEUS_ENABLED=true

# ==============================================
# EMAIL (Optional)
# ==============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@your-domain.com

# ==============================================
# REDIS (Optional - Caching)
# ==============================================
REDIS_URL=redis://redis:6379/0
REDIS_ENABLED=true

# ==============================================
# RATE LIMITING
# ==============================================
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

---

## Database Setup

### Automatic Setup (Docker)

Database is automatically initialized when using Docker Compose.

### Manual Setup (PostgreSQL)
```bash
# Create database
createdb agentic_research

# Run migrations
cd backend
python -m alembic upgrade head

# Verify
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

### Backup & Restore
```bash
# Backup
docker exec agentic-postgres pg_dump -U postgres agentic_research > backup.sql

# Restore
docker exec -i agentic-postgres psql -U postgres agentic_research < backup.sql
```

---

## Production Deployment

### Option 1: Docker Compose (Single Server)

**Best for:** Small teams, staging environments
```bash
# 1. Configure environment
cp .env.example .env
nano .env

# 2. Start services
docker-compose up -d

# 3. Enable auto-restart
docker-compose up -d --force-recreate
```

### Option 2: Kubernetes

**Best for:** Large scale, high availability
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic-backend
  template:
    metadata:
      labels:
        app: agentic-backend
    spec:
      containers:
      - name: backend
        image: your-registry/agentic-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: database-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

Deploy:
```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f deployment/agentic-backend
```

### Option 3: AWS ECS/Fargate

**Best for:** AWS-native deployments
```bash
# 1. Build and push images
docker build -t agentic-backend ./backend
docker tag agentic-backend:latest /agentic-backend:latest
docker push /agentic-backend:latest

# 2. Create ECS task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster agentic-cluster \
  --service-name agentic-backend \
  --task-definition agentic-backend \
  --desired-count 2 \
  --launch-type FARGATE
```

---

## Monitoring & Logging

### Application Logs
```bash
# View all logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Save logs to file
docker-compose logs > logs_$(date +%Y%m%d).txt
```

### Metrics Endpoint
```bash
# Application metrics
curl http://localhost:8000/metrics

# Returns:
# {
#   "uptime_seconds": 3600,
#   "counters": {
#     "http_requests_total": {...},
#     "agent_executions_total": {...}
#   },
#   "histograms": {
#     "http_request_duration_ms": {...}
#   }
# }
```

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health | jq '.database'

# AI connectivity
curl http://localhost:8000/health | jq '.ai'
```

### Prometheus Integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentic-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - backend
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale backend=3
```

### Database Connection Pooling
```python
# backend/.env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
```

### Caching with Redis
```yaml
# Enable Redis
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string
docker-compose exec backend env | grep DATABASE_URL

# Test connection
docker-compose exec postgres psql -U postgres -d agentic_research -c "\dt"
```

**2. Ollama Model Not Found**
```bash
# Pull model
docker-compose exec ollama ollama pull llama3.2:3b

# List available models
docker-compose exec ollama ollama list
```

**3. Frontend Can't Connect to Backend**
```bash
# Check CORS settings
grep CORS_ORIGINS .env

# Check network
docker-compose exec frontend ping backend

# Check API URL
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
```

**4. High Memory Usage**
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart

# Reduce workers
docker-compose up -d --scale backend=1
```

### Debug Mode
```bash
# Enable debug mode
echo "DEBUG=True" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart
docker-compose restart backend

# View detailed logs
docker-compose logs -f backend
```

### Performance Profiling
```bash
# Install profiling tools
pip install py-spy

# Profile running process
py-spy top --pid $(pgrep -f "uvicorn")

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f "uvicorn")
```

---

## Security Checklist

- [ ] Changed default `JWT_SECRET_KEY`
- [ ] Changed default `POSTGRES_PASSWORD`
- [ ] Enabled HTTPS (SSL certificates)
- [ ] Configured firewall rules
- [ ] Set up rate limiting
- [ ] Enabled CORS for specific domains only
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Secrets stored in vault (not `.env` in production)
- [ ] Monitoring and alerts configured

---

## Support

- **Documentation:** https://docs.your-domain.com
- **Issues:** https://github.com/your-org/agentic-research-ai/issues
- **Email:** support@your-domain.com

---

**🎉 Deployment Complete!**

Your Agentic Research AI system is now running in production.
