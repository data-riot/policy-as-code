# Deployment Guide

This guide covers deploying the Decision Layer in various environments.

## Prerequisites

- **Python 3.8+** - Required Python version
- **Memory** - Minimum 2GB RAM (4GB+ recommended)
- **Storage** - Minimum 10GB available space
- **PostgreSQL** (optional) - For production database backend

## Local Development

```bash
# Clone and setup
git clone https://github.com/data-riot/policy-as-code.git
cd policy-as-code

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install and initialize
pip install -r requirements.txt
pip install -e .
policy-as-code init

# Start the API server
python run_api.py
```

## Docker Deployment

### Single Container

```bash
# Build and run
docker build -t policy-as-code .
docker run -d --name policy-as-code -p 8000:8000 policy-as-code
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DECISION_LAYER_STORAGE_BACKEND=postgresql
      - DECISION_LAYER_DATABASE_URL=postgresql://decision_user:password@db:5432/policy_as_code
    depends_on:
      - db
    volumes:
      - ./traces:/app/traces

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=policy_as_code
      - POSTGRES_USER=decision_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Deploy with:
```bash
docker-compose up -d
```

## Production Deployment

### Environment Variables

```bash
# Database
DECISION_LAYER_DATABASE_URL=postgresql://user:pass@host:5432/policy_as_code

# Security
DECISION_LAYER_API_KEY=changeme-secret-api-key
DECISION_LAYER_SECRET_KEY=changeme-secret-key

# Performance
DECISION_LAYER_RATE_LIMIT_REQUESTS=1000
DECISION_LAYER_RATE_LIMIT_WINDOW=60
```

### Production Checklist

- [ ] **SSL/TLS Configuration** - Enable HTTPS for all endpoints
- [ ] **API Key Management** - Secure API key storage and rotation
- [ ] **Database Security** - Encrypted connections and access controls
- [ ] **Load Balancing** - Configure load balancers for high availability
- [ ] **Monitoring** - Set up health checks and logging
- [ ] **Backup Strategy** - Automated database backups

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check logs
docker logs policy-as-code-api

# Monitor resource usage
docker stats policy-as-code-api
```

## Cloud Deployment

### AWS ECS

Use the provided CloudFormation template or deploy via ECS console with:
- Task definition with appropriate CPU/memory
- Load balancer configuration
- RDS PostgreSQL database
- Security groups and IAM roles

### Kubernetes

Deploy using the provided Kubernetes manifests:
- Namespace and ConfigMap
- PostgreSQL deployment
- Application deployment
- Ingress configuration

### Google Cloud Run

Deploy as a serverless container:
```bash
gcloud run deploy policy-as-code \
  --image gcr.io/project-id/policy-as-code:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Troubleshooting

### Common Issues

**Container startup issues**: Check logs with `docker logs <container-id>`

**Database connection issues**: Verify connection string and network connectivity

**Performance issues**: Check resource utilization and optimize database queries

### Monitoring

- **Health endpoint**: `/health`
- **Metrics**: Application and infrastructure metrics
- **Logging**: Structured logging with correlation IDs
- **Alerting**: Set up alerts for critical issues

## Next Steps

- **Read the [Development Guide](development.md)** for detailed setup
- **Check the [API Reference](api.md)** for integration options
- **Review the [Architecture Documentation](architecture.md)** for system design
