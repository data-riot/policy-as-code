# Deployment Guide

This guide covers deploying the Decision Layer in various environments, from development to production.

## Deployment Overview

The Decision Layer can be deployed in multiple ways:

- **Local Development** - For development and testing
- **Docker** - Containerized deployment
- **Kubernetes** - Orchestrated container deployment
- **Cloud Platforms** - AWS, Azure, GCP deployment
- **On-Premises** - Traditional server deployment

## Prerequisites

### System Requirements

- **Python 3.8+** - Required Python version
- **Memory** - Minimum 2GB RAM (4GB+ recommended)
- **Storage** - Minimum 10GB available space
- **Network** - Internet access for dependencies and external integrations

### Dependencies

- **PostgreSQL** (optional) - For production database backend
- **Redis** (optional) - For caching and session storage
- **Neo4j** (optional) - For ontology and knowledge graph integration

## Local Development Deployment

### Quick Start

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Initialize the system
decision-layer init

# Start the API server (web interface not implemented)
python run_api.py
```

### Development Configuration

Create `config.dev.yaml`:

```yaml
# Development configuration
core:
  storage:
    backend: file
    path: ./dev_registry

  trace:
    directory: ./dev_traces
    level: DEBUG
    retention_days: 7

security:
  enable_auth: false
  rate_limiting:
    enabled: false

integrations:
  llm:
    provider: mock
  ontology:
    provider: mock
  knowledge_graph:
    provider: mock

web:
  theme: light
  dashboard:
    auto_refresh: 10
```

## Docker Deployment

### Single Container Deployment

#### Dockerfile

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p registry traces config data logs

# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV DECISION_LAYER_STORAGE_BACKEND=file
ENV DECISION_LAYER_TRACE_DIR=/app/traces

# Initialize the system
RUN decision-layer init

# Start the application
CMD ["python", "run_api.py"]
```

#### Build and Run

```bash
# Build the image
docker build -t decision-layer .

# Run the container
docker run -d \
  --name decision-layer \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/traces:/app/traces \
  decision-layer
```

### Multi-Container Deployment with Docker Compose

#### docker-compose.yml

```yaml
version: '3.8'

services:
  # Decision Layer API
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DECISION_LAYER_STORAGE_BACKEND=postgresql
      - DECISION_LAYER_DATABASE_URL=postgresql://decision_user:password@db:5432/decision_layer
      - DECISION_LAYER_REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./traces:/app/traces
      - ./config:/app/config
    restart: unless-stopped

  # PostgreSQL Database
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=decision_layer
      - POSTGRES_USER=decision_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Neo4j (for ontology and knowledge graph)
  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
```

#### Database Initialization

Create `init.sql`:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create traces table
CREATE TABLE IF NOT EXISTS traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    function_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    input_hash VARCHAR(64),
    output_hash VARCHAR(64),
    execution_time_ms INTEGER,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_traces_function_id ON traces(function_id);
CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);

-- Create functions table
CREATE TABLE IF NOT EXISTS functions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    function_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    logic_code TEXT NOT NULL,
    schema JSONB,
    metadata JSONB,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(function_id, version)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_functions_function_id ON functions(function_id);
CREATE INDEX IF NOT EXISTS idx_functions_status ON functions(status);
```

#### Deploy with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Kubernetes Deployment

### Namespace and ConfigMap

#### namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: decision-layer
```

#### configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: decision-layer-config
  namespace: decision-layer
data:
  config.yaml: |
    core:
      storage:
        backend: postgresql
      trace:
        directory: /app/traces
        level: INFO
        retention_days: 90

    security:
      enable_auth: true
      rate_limiting:
        enabled: true
        requests_per_minute: 1000

    integrations:
      llm:
        provider: openai
      ontology:
        provider: neo4j
      knowledge_graph:
        provider: neo4j
```

### Database Deployment

#### postgresql-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: decision-layer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: decision_layer
        - name: POSTGRES_USER
          value: decision_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgresql-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgresql-data
        persistentVolumeClaim:
          claimName: postgresql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: decision-layer
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-pvc
  namespace: decision-layer
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Application Deployment

#### decision-layer-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: decision-layer-api
  namespace: decision-layer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: decision-layer-api
  template:
    metadata:
      labels:
        app: decision-layer-api
    spec:
      containers:
      - name: api
        image: decision-layer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DECISION_LAYER_DATABASE_URL
          value: postgresql://decision_user:$(POSTGRES_PASSWORD)@postgresql:5432/decision_layer
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        - name: DECISION_LAYER_API_KEY
          valueFrom:
            secretKeyRef:
              name: decision-layer-secret
              key: api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: traces
          mountPath: /app/traces
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: decision-layer-config
      - name: traces
        persistentVolumeClaim:
          claimName: traces-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: decision-layer-api
  namespace: decision-layer
spec:
  selector:
    app: decision-layer-api
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: traces-pvc
  namespace: decision-layer
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
```

### Ingress Configuration

#### ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: decision-layer-ingress
  namespace: decision-layer
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.decision-layer.example.com
    - web.decision-layer.example.com
    secretName: decision-layer-tls
  rules:
  - host: api.decision-layer.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: decision-layer-api
            port:
              number: 8000
  - host: web.decision-layer.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: decision-layer-web
            port:
              number: 8501
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
kubectl create secret generic postgresql-secret \
  --from-literal=password=your-secure-password \
  --namespace=decision-layer

kubectl create secret generic decision-layer-secret \
  --from-literal=api-key=your-api-key \
  --namespace=decision-layer

# Deploy database
kubectl apply -f postgresql-deployment.yaml

# Deploy application
kubectl apply -f decision-layer-deployment.yaml

# Deploy ingress
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n decision-layer
kubectl get services -n decision-layer
```

## Cloud Platform Deployment

### AWS Deployment

#### ECS with Fargate

```yaml
# task-definition.json
{
  "family": "decision-layer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/decision-layer-task-role",
  "containerDefinitions": [
    {
      "name": "decision-layer-api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/decision-layer:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DECISION_LAYER_DATABASE_URL",
          "value": "postgresql://user:pass@your-rds-endpoint:5432/decision_layer"
        },
        {
          "name": "DECISION_LAYER_API_KEY",
          "value": "your-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/decision-layer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### CloudFormation Template

```yaml
# cloudformation.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Decision Layer ECS Deployment'

Parameters:
  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: VPC ID

  SubnetIds:
    Type: List<AWS::EC2::Subnet::Id>
    Description: Subnet IDs

Resources:
  # ECS Cluster
  DecisionLayerCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: decision-layer-cluster
      CapacityProviders:
        - FARGATE
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1

  # RDS Database
  DecisionLayerDB:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: decision-layer-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '15.4'
      MasterUsername: decision_user
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: 20
      StorageType: gp2
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      DBSubnetGroupName: !Ref DBSubnetGroup

  # Application Load Balancer
  DecisionLayerALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: decision-layer-alb
      Scheme: internet-facing
      Type: application
      Subnets: !Ref SubnetIds
      SecurityGroups:
        - !Ref ALBSecurityGroup

  # ECS Service
  DecisionLayerService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: decision-layer-service
      Cluster: !Ref DecisionLayerCluster
      TaskDefinition: !Ref DecisionLayerTaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED
          SecurityGroups:
            - !Ref ECSSecurityGroup
          Subnets: !Ref SubnetIds
      LoadBalancers:
        - ContainerName: decision-layer-api
          ContainerPort: 8000
          TargetGroupArn: !Ref DecisionLayerTargetGroup

Outputs:
  LoadBalancerDNS:
    Description: DNS name of the load balancer
    Value: !GetAtt DecisionLayerALB.DNSName
```

### Azure Deployment

#### Azure Container Instances

```yaml
# azure-deployment.yaml
apiVersion: 2019-12-01
location: eastus
name: decision-layer
properties:
  containers:
  - name: decision-layer-api
    properties:
      image: decision-layer:latest
      ports:
      - port: 8000
      environmentVariables:
      - name: DECISION_LAYER_DATABASE_URL
        value: "postgresql://user:pass@your-azure-postgres:5432/decision_layer"
      - name: DECISION_LAYER_API_KEY
        secureValue: "your-api-key"
      resources:
        requests:
          memoryInGB: 1
          cpu: 0.5
        limits:
          memoryInGB: 2
          cpu: 1
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 8000
```

### Google Cloud Platform Deployment

#### Cloud Run

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: decision-layer-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/your-project/decision-layer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DECISION_LAYER_DATABASE_URL
          value: "postgresql://user:pass@your-cloud-sql:5432/decision_layer"
        - name: DECISION_LAYER_API_KEY
          valueFrom:
            secretKeyRef:
              name: decision-layer-secret
              key: api-key
        resources:
          limits:
            cpu: "1"
            memory: "2Gi"
          requests:
            cpu: "500m"
            memory: "1Gi"
```

## Production Deployment Checklist

### Security

- [ ] **SSL/TLS Configuration** - Enable HTTPS for all endpoints
- [ ] **API Key Management** - Secure API key storage and rotation
- [ ] **Database Security** - Encrypted connections and access controls
- [ ] **Network Security** - Firewall rules and VPC configuration
- [ ] **Secret Management** - Use cloud secret management services

### Performance

- [ ] **Load Balancing** - Configure load balancers for high availability
- [ ] **Auto-scaling** - Set up auto-scaling policies
- [ ] **Caching** - Configure Redis or similar caching layer
- [ ] **Database Optimization** - Indexes and connection pooling
- [ ] **CDN** - Content delivery network for static assets

### Monitoring

- [ ] **Health Checks** - Configure health check endpoints
- [ ] **Logging** - Centralized logging with structured logs
- [ ] **Metrics** - Application and infrastructure metrics
- [ ] **Alerting** - Set up alerts for critical issues
- [ ] **Tracing** - Distributed tracing for request flows

### Backup and Recovery

- [ ] **Database Backups** - Automated backup schedules
- [ ] **Configuration Backups** - Version control for configurations
- [ ] **Disaster Recovery** - Multi-region deployment strategy
- [ ] **Data Retention** - Configure appropriate retention policies
- [ ] **Recovery Testing** - Regular recovery procedure testing

## Troubleshooting

### Common Deployment Issues

#### Container Startup Issues

**Problem**: Containers failing to start

**Solutions**:
1. Check container logs: `docker logs <container-id>`
2. Verify environment variables
3. Check resource limits
4. Validate configuration files

#### Database Connection Issues

**Problem**: Cannot connect to database

**Solutions**:
1. Verify connection string format
2. Check network connectivity
3. Validate credentials
4. Test connection manually

#### Performance Issues

**Problem**: Slow response times

**Solutions**:
1. Check resource utilization
2. Optimize database queries
3. Configure caching
4. Scale horizontally

### Monitoring and Debugging

```bash
# Check application health
curl http://localhost:8000/health

# View application logs
docker logs decision-layer-api

# Check resource usage
docker stats decision-layer-api

# Monitor database connections
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"

# Check Kubernetes pod status
kubectl get pods -n decision-layer
kubectl logs -f deployment/decision-layer-api -n decision-layer
```

## Next Steps

- **Read the [Configuration Guide](configuration.md)** for detailed configuration options
- **Check the [Architecture Documentation](architecture.md)** for system design
- **Review the [API Reference](api.md)** for integration options
- **Explore the [Examples](../examples/)** for deployment examples
