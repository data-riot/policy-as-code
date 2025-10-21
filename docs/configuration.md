# Configuration Guide

The Decision Layer provides extensive configuration options to customize behavior for different environments and use cases.

## Configuration Overview

Configuration can be managed through:
- **Environment Variables** - For sensitive data and deployment-specific settings
- **Configuration Files** - For application settings and defaults
- **Runtime Configuration** - For dynamic settings that can be changed without restart

## Environment Variables

### Core Configuration

```bash
# Storage Configuration
DECISION_LAYER_STORAGE_BACKEND=file                    # file, postgresql, s3
DECISION_LAYER_STORAGE_PATH=./registry                 # Storage path for file backend
DECISION_LAYER_DATABASE_URL=postgresql://user:pass@localhost/db  # Database URL

# Trace Configuration
DECISION_LAYER_TRACE_DIR=./traces                      # Trace storage directory
DECISION_LAYER_TRACE_LEVEL=INFO                        # Trace logging level
DECISION_LAYER_TRACE_RETENTION_DAYS=90                 # Trace retention period

# Security Configuration
DECISION_LAYER_API_KEY=your-secret-api-key             # API authentication key
DECISION_LAYER_SECRET_KEY=your-secret-key              # Application secret key
DECISION_LAYER_ENABLE_AUTH=true                        # Enable authentication
DECISION_LAYER_SESSION_TIMEOUT=3600                    # Session timeout in seconds

# Performance Configuration
DECISION_LAYER_MAX_INPUT_SIZE=1048576                  # Max input size in bytes (1MB)
DECISION_LAYER_RATE_LIMIT_REQUESTS=100                 # Rate limit requests per window
DECISION_LAYER_RATE_LIMIT_WINDOW=60                    # Rate limit window in seconds
DECISION_LAYER_CACHE_SIZE=1000                         # Cache size for function storage
```

### Cross-Domain Integration

```bash
# LLM Integration
DECISION_LAYER_LLM_PROVIDER=mock                       # mock, openai, anthropic, azure
DECISION_LAYER_OPENAI_API_KEY=your-openai-key          # OpenAI API key
DECISION_LAYER_ANTHROPIC_API_KEY=your-anthropic-key    # Anthropic API key
DECISION_LAYER_AZURE_OPENAI_ENDPOINT=your-endpoint     # Azure OpenAI endpoint

# Ontology Integration
DECISION_LAYER_ONTOLOGY_PROVIDER=mock                  # mock, owl, neo4j
DECISION_LAYER_ONTOLOGY_FILE=./ontologies/domain.owl   # OWL ontology file
DECISION_LAYER_NEO4J_URI=bolt://localhost:7687         # Neo4j connection URI
DECISION_LAYER_NEO4J_USER=neo4j                        # Neo4j username
DECISION_LAYER_NEO4J_PASSWORD=password                 # Neo4j password

# Knowledge Graph Integration
DECISION_LAYER_KG_PROVIDER=mock                        # mock, neo4j, amazon_neptune
DECISION_LAYER_NEPTUNE_ENDPOINT=your-neptune-endpoint  # Amazon Neptune endpoint
DECISION_LAYER_NEPTUNE_PORT=8182                       # Neptune port
DECISION_LAYER_NEPTUNE_REGION=us-east-1                # Neptune region
```

### Web Interface Configuration

```bash
# Web Server Configuration
DECISION_LAYER_WEB_HOST=0.0.0.0                        # Web interface host
DECISION_LAYER_WEB_PORT=8501                           # Web interface port
DECISION_LAYER_WEB_TITLE="Decision Layer"              # Web interface title
DECISION_LAYER_WEB_THEME=light                         # light, dark, auto

# API Server Configuration
DECISION_LAYER_API_HOST=0.0.0.0                        # API server host
DECISION_LAYER_API_PORT=8000                           # API server port
DECISION_LAYER_API_WORKERS=4                           # Number of API workers
```

### Logging Configuration

```bash
# Logging Settings
DECISION_LAYER_LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
DECISION_LAYER_LOG_FILE=logs/decision_layer.log        # Log file path
DECISION_LAYER_LOG_FORMAT=json                         # json, text
DECISION_LAYER_LOG_MAX_SIZE=10485760                   # Max log file size (10MB)
DECISION_LAYER_LOG_BACKUP_COUNT=5                      # Number of backup log files
```

## Configuration Files

### Main Configuration File (`config.yaml`)

```yaml
# Core Configuration
core:
  # Storage settings
  storage:
    backend: file  # file, postgresql, s3
    path: ./registry
    database_url: null  # Only for postgresql backend

  # Trace settings
  trace:
    directory: ./traces
    level: INFO
    retention_days: 90
    max_file_size: 10485760  # 10MB

  # Performance settings
  performance:
    max_input_size: 1048576  # 1MB
    cache_size: 1000
    execution_timeout: 300  # 5 minutes

# Security Configuration
security:
  # Authentication
  enable_auth: false
  api_key: null  # Set via environment variable
  secret_key: null  # Set via environment variable
  session_timeout: 3600  # 1 hour

  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 100
    burst_size: 10

  # Input validation
  input_validation:
    enabled: true
    sanitize_inputs: true
    max_nesting_depth: 10

  # Output validation
  output_validation:
    enabled: true
    sanitize_outputs: true

# Plugin Configuration
plugins:
  # Validation plugins
  validation:
    enabled: true
    plugins:
      - name: schema_validation
        enabled: true
      - name: custom_validation
        enabled: false
        config:
          custom_rules: []

  # Tracing plugins
  tracing:
    enabled: true
    plugins:
      - name: file_tracing
        enabled: true
        config:
          directory: ./traces
      - name: database_tracing
        enabled: false
        config:
          table_name: traces

  # Caching plugins
  caching:
    enabled: true
    plugins:
      - name: memory_cache
        enabled: true
        config:
          max_size: 1000
          ttl: 3600

# Cross-Domain Integration
integrations:
  # LLM Integration
  llm:
    provider: mock  # mock, openai, anthropic, azure
    config:
      # OpenAI configuration
      openai:
        api_key: null  # Set via environment variable
        model: gpt-4
        max_tokens: 2000
        temperature: 0.1

      # Anthropic configuration
      anthropic:
        api_key: null  # Set via environment variable
        model: claude-3-sonnet-20240229
        max_tokens: 2000

      # Azure OpenAI configuration
      azure:
        endpoint: null  # Set via environment variable
        api_key: null  # Set via environment variable
        deployment_name: gpt-4
        api_version: 2024-02-15-preview

  # Ontology Integration
  ontology:
    provider: mock  # mock, owl, neo4j
    config:
      # OWL configuration
      owl:
        file_path: ./ontologies/domain.owl
        reasoner: pellet  # pellet, hermit, jfact

      # Neo4j configuration
      neo4j:
        uri: bolt://localhost:7687
        username: neo4j
        password: null  # Set via environment variable
        database: neo4j

  # Knowledge Graph Integration
  knowledge_graph:
    provider: mock  # mock, neo4j, amazon_neptune
    config:
      # Neo4j configuration
      neo4j:
        uri: bolt://localhost:7687
        username: neo4j
        password: null  # Set via environment variable
        database: neo4j

      # Amazon Neptune configuration
      neptune:
        endpoint: null  # Set via environment variable
        port: 8182
        region: us-east-1
        iam_auth: false

# Web Interface Configuration
web:
  # General settings
  title: "Decision Layer"
  theme: light  # light, dark, auto
  layout: wide  # wide, centered

  # Dashboard settings
  dashboard:
    auto_refresh: 30  # seconds
    default_widgets:
      - status
      - functions
      - recent_traces
      - performance_metrics

  # Editor settings
  editor:
    theme: monokai  # editor theme
    font_size: 14
    line_numbers: true
    auto_complete: true
    word_wrap: false

  # Trace viewer settings
  traces:
    page_size: 50
    default_sort: timestamp
    show_input_output: true
    enable_search: true

# API Configuration
api:
  # Server settings
  host: 0.0.0.0
  port: 8000
  workers: 4

  # CORS settings
  cors:
    enabled: true
    allowed_origins:
      - http://localhost:3000
      - http://localhost:8501
    allowed_methods:
      - GET
      - POST
      - PUT
      - DELETE
    allowed_headers:
      - Content-Type
      - Authorization
      - X-API-Key

  # Documentation settings
  docs:
    enabled: true
    title: "Decision Layer API"
    version: "2.0.0"
    description: "Decision Layer REST API"

# CLI Configuration
cli:
  # Output settings
  default_format: table  # table, json, yaml
  enable_colors: true
  verbose_output: false

  # Command settings
  commands:
    list:
      default_limit: 50
      enable_pagination: true
    traces:
      default_limit: 100
      enable_pagination: true
    test:
      enable_parallel: true
      max_workers: 4

# Monitoring Configuration
monitoring:
  # Metrics collection
  metrics:
    enabled: true
    endpoint: /metrics
    format: prometheus  # prometheus, json

  # Health checks
  health:
    enabled: true
    endpoint: /health
    checks:
      - storage
      - registry
      - traces

  # Alerting
  alerts:
    enabled: false
    webhook_url: null
    slack_webhook: null
    email:
      smtp_server: null
      smtp_port: 587
      username: null
      password: null
      from_address: null
      to_addresses: []
```

### Environment-Specific Configuration

#### Development Configuration (`config.dev.yaml`)

```yaml
# Development-specific settings
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
    auto_refresh: 10  # Faster refresh for development
```

#### Production Configuration (`config.prod.yaml`)

```yaml
# Production-specific settings
core:
  storage:
    backend: postgresql
    database_url: ${DATABASE_URL}

  trace:
    directory: /var/log/decision_layer/traces
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
    config:
      openai:
        api_key: ${OPENAI_API_KEY}
        model: gpt-4
  ontology:
    provider: neo4j
    config:
      neo4j:
        uri: ${NEO4J_URI}
        username: ${NEO4J_USER}
        password: ${NEO4J_PASSWORD}
  knowledge_graph:
    provider: amazon_neptune
    config:
      neptune:
        endpoint: ${NEPTUNE_ENDPOINT}
        region: ${NEPTUNE_REGION}

web:
  theme: auto
  dashboard:
    auto_refresh: 60  # Slower refresh for production

monitoring:
  metrics:
    enabled: true
  health:
    enabled: true
  alerts:
    enabled: true
    webhook_url: ${ALERT_WEBHOOK_URL}
```

## Runtime Configuration

### Configuration Management API

```python
from decision_layer.config import ConfigManager

# Get configuration manager
config = ConfigManager()

# Get configuration value
storage_backend = config.get('core.storage.backend')
api_key = config.get('security.api_key')

# Set configuration value
config.set('core.storage.backend', 'postgresql')
config.set('security.api_key', 'new-api-key')

# Update multiple values
config.update({
    'core.storage.backend': 'postgresql',
    'core.storage.database_url': 'postgresql://user:pass@localhost/db',
    'security.enable_auth': True
})

# Reload configuration
config.reload()

# Save configuration
config.save()
```

### Dynamic Configuration Updates

```python
from decision_layer import DecisionEngine

# Create engine with custom configuration
engine = DecisionEngine()

# Update configuration at runtime
engine.update_config({
    'performance.max_input_size': 2097152,  # 2MB
    'security.rate_limiting.requests_per_minute': 200
})

# Get current configuration
current_config = engine.get_config()
print(f"Current rate limit: {current_config['security']['rate_limiting']['requests_per_minute']}")
```

## Configuration Validation

### Schema Validation

The configuration system validates all settings against a schema:

```python
from decision_layer.config import validate_config

# Validate configuration
try:
    validate_config(config_data)
    print("✅ Configuration is valid")
except ValidationError as e:
    print(f"❌ Configuration error: {e}")
```

### Configuration Testing

```bash
# Test configuration
decision-layer config test

# Validate specific configuration file
decision-layer config validate config.yaml

# Check configuration for issues
decision-layer config check
```

## Configuration Best Practices

### Security

1. **Never commit secrets to version control**
   ```bash
   # Use environment variables for secrets
   export DECISION_LAYER_API_KEY=your-secret-key
   export DECISION_LAYER_DATABASE_URL=postgresql://user:pass@localhost/db
   ```

2. **Use different configurations for different environments**
   ```bash
   # Development
   cp config.dev.yaml config.yaml

   # Production
   cp config.prod.yaml config.yaml
   ```

3. **Rotate secrets regularly**
   ```bash
   # Generate new API key
   openssl rand -hex 32
   ```

### Performance

1. **Optimize storage settings**
   ```yaml
   core:
     storage:
       # Use PostgreSQL for production
       backend: postgresql
       # Use file storage for development
       backend: file
   ```

2. **Configure appropriate cache sizes**
   ```yaml
   performance:
     cache_size: 1000  # Adjust based on available memory
   ```

3. **Set appropriate rate limits**
   ```yaml
   security:
     rate_limiting:
       requests_per_minute: 100  # Adjust based on capacity
   ```

### Monitoring

1. **Enable metrics collection**
   ```yaml
   monitoring:
     metrics:
       enabled: true
   ```

2. **Configure health checks**
   ```yaml
   monitoring:
     health:
       enabled: true
       checks:
         - storage
         - registry
         - traces
   ```

3. **Set up alerting**
   ```yaml
   monitoring:
     alerts:
       enabled: true
       webhook_url: ${ALERT_WEBHOOK_URL}
   ```

## Troubleshooting

### Common Configuration Issues

#### Configuration Not Loading

**Problem**: Configuration changes not taking effect

**Solutions**:
1. Check file permissions: `ls -la config.yaml`
2. Verify YAML syntax: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
3. Restart the application after configuration changes
4. Check environment variable precedence

#### Environment Variable Issues

**Problem**: Environment variables not being read

**Solutions**:
1. Verify variable names: Use `DECISION_LAYER_` prefix
2. Check variable scope: Export in the correct shell
3. Restart the application after setting variables
4. Use `.env` file for local development

#### Database Connection Issues

**Problem**: Cannot connect to database

**Solutions**:
1. Verify connection string format
2. Check database server status
3. Verify credentials and permissions
4. Test connection manually: `psql $DATABASE_URL`

### Configuration Debugging

```bash
# Show current configuration
decision-layer config show

# Show configuration with environment variables
decision-layer config show --include-env

# Show configuration sources
decision-layer config sources

# Validate configuration
decision-layer config validate

# Test configuration
decision-layer config test
```

## Next Steps

- **Read the [Installation Guide](installation.md)** for setup instructions
- **Check the [CLI Reference](cli.md)** for configuration commands
- **Review the [Architecture Documentation](architecture.md)** for system design
- **Explore the [Examples](../examples/)** for configuration examples
