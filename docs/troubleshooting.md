# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Decision Layer.

## Quick Diagnosis

### System Health Check

```bash
# Check system status
decision-layer status

# Check API health
curl http://localhost:8000/health

# Check web interface
curl http://localhost:8501

# Check logs
tail -f logs/decision_layer.log
```

### Common Error Patterns

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `ModuleNotFoundError` | Missing dependencies | Install requirements |
| `Connection refused` | Service not running | Start the service |
| `Permission denied` | File permissions | Fix permissions |
| `Port already in use` | Port conflict | Change port or stop conflicting service |
| `ValidationError` | Invalid input data | Check input format |

## Installation Issues

### Python Environment Problems

#### Problem: `python` command not found

**Symptoms**:
```bash
$ python --version
bash: python: command not found
```

**Solutions**:
1. **Install Python 3.8+**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # macOS
   brew install python3

   # Windows
   # Download from python.org
   ```

2. **Use python3 explicitly**:
   ```bash
   python3 --version
   python3 -m pip install -r requirements.txt
   ```

3. **Create alias**:
   ```bash
   echo 'alias python=python3' >> ~/.bashrc
   source ~/.bashrc
   ```

#### Problem: Virtual environment issues

**Symptoms**:
```bash
$ pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions**:
1. **Create fresh virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Check Python version**:
   ```bash
   python --version  # Should be 3.8+
   ```

3. **Clear pip cache**:
   ```bash
   pip cache purge
   pip install -r requirements.txt
   ```

### Dependency Installation Issues

#### Problem: Package installation fails

**Symptoms**:
```bash
$ pip install -e .
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions**:
1. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **Install system dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt install build-essential python3-dev
   ```

3. **Use alternative package manager**:
   ```bash
   # Try conda instead of pip
   conda install -c conda-forge decision-layer
   ```

4. **Install from source**:
   ```bash
   git clone https://github.com/data-riot/decision-layer.git
   cd decision-layer
   pip install -e .
   ```

## Runtime Issues

### Service Startup Problems

#### Problem: API server won't start

**Symptoms**:
```bash
$ python run_api.py
Error: Address already in use
```

**Solutions**:
1. **Check if port is in use**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000

   # Kill the process
   kill -9 <PID>
   ```

2. **Use different port**:
   ```bash
   # Set environment variable
   export DECISION_LAYER_API_PORT=8001
   python run_api.py
   ```

3. **Check for zombie processes**:
   ```bash
   ps aux | grep python
   pkill -f "run_api.py"
   ```

#### Problem: Web interface won't start

**Symptoms**:
```bash
$ python run_ui.py
Error: Port 8501 is already in use
```

**Solutions**:
1. **Check Streamlit processes**:
   ```bash
   ps aux | grep streamlit
   pkill -f streamlit
   ```

2. **Use different port**:
   ```bash
   streamlit run streamlit_app.py --server.port 8502
   ```

3. **Check for conflicting services**:
   ```bash
   netstat -tulpn | grep 8501
   ```

### Database Connection Issues

#### Problem: Cannot connect to PostgreSQL

**Symptoms**:
```bash
Error: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

**Solutions**:
1. **Check PostgreSQL status**:
   ```bash
   # Ubuntu/Debian
   sudo systemctl status postgresql

   # macOS
   brew services list | grep postgresql

   # Start if not running
   sudo systemctl start postgresql
   ```

2. **Verify connection string**:
   ```bash
   # Test connection
   psql postgresql://user:pass@localhost:5432/dbname
   ```

3. **Check PostgreSQL configuration**:
   ```bash
   # Check pg_hba.conf
   sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v '^#'

   # Restart PostgreSQL
   sudo systemctl restart postgresql
   ```

4. **Create database and user**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE decision_layer;
   CREATE USER decision_user WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE decision_layer TO decision_user;
   \q
   ```

### Function Execution Issues

#### Problem: Function not found

**Symptoms**:
```bash
Error: Function 'loan_approval' not found
```

**Solutions**:
1. **Check if function is deployed**:
   ```bash
   decision-layer list
   ```

2. **Deploy the function**:
   ```bash
   decision-layer deploy loan_approval 1.0 loan_approval.py
   ```

3. **Check function registry**:
   ```bash
   decision-layer info loan_approval
   ```

#### Problem: Function execution fails

**Symptoms**:
```bash
Error: Execution failed for loan_approval v1.0
```

**Solutions**:
1. **Check function code**:
   ```bash
   # View function code
   decision-layer info loan_approval --version 1.0
   ```

2. **Test function manually**:
   ```bash
   # Test with simple input
   decision-layer test loan_approval test_input.json
   ```

3. **Check logs for details**:
   ```bash
   tail -f logs/decision_layer.log
   ```

4. **Validate input data**:
   ```bash
   # Check input schema
   decision-layer info loan_approval --format json | jq '.schema.input_schema'
   ```

### Validation Issues

#### Problem: Input validation fails

**Symptoms**:
```bash
Error: Input validation failed
Field 'credit_score': Value must be between 300 and 850
```

**Solutions**:
1. **Check input schema**:
   ```bash
   decision-layer info loan_approval --format json | jq '.schema.input_schema'
   ```

2. **Validate input manually**:
   ```python
   from decision_layer.schemas import SchemaValidator

   # Create validator
   validator = SchemaValidator(schema)

   # Validate input
   try:
       validator.validate_input(input_data)
       print("✅ Input is valid")
   except ValidationError as e:
       print(f"❌ Validation error: {e}")
   ```

3. **Fix input data**:
   ```json
   {
     "credit_score": 750,  // Must be 300-850
     "income": 75000,      // Must be positive
     "age": 30            // Must be 18+
   }
   ```

#### Problem: Output validation fails

**Symptoms**:
```bash
Error: Output validation failed
Field 'approved': Required field missing
```

**Solutions**:
1. **Check output schema**:
   ```bash
   decision-layer info loan_approval --format json | jq '.schema.output_schema'
   ```

2. **Fix function output**:
   ```python
   def decision_function(input_data, context):
       # Ensure all required fields are present
       return {
           "approved": True,      # Required boolean
           "reason": "Approved",  # Required string
           "risk_level": "low"    # Required enum
       }
   ```

## Configuration Issues

### Environment Variable Problems

#### Problem: Environment variables not read

**Symptoms**:
```bash
# Configuration shows default values instead of environment variables
decision-layer config show
```

**Solutions**:
1. **Check variable names**:
   ```bash
   # Use DECISION_LAYER_ prefix
   export DECISION_LAYER_API_KEY=your-key
   export DECISION_LAYER_DATABASE_URL=postgresql://...
   ```

2. **Verify variable scope**:
   ```bash
   # Check if variables are set
   env | grep DECISION_LAYER

   # Set in current shell
   export DECISION_LAYER_DEBUG=true
   ```

3. **Use .env file**:
   ```bash
   # Create .env file
   echo "DECISION_LAYER_API_KEY=your-key" > .env
   echo "DECISION_LAYER_DATABASE_URL=postgresql://..." >> .env

   # Load .env file
   source .env
   ```

### Configuration File Issues

#### Problem: Configuration file not found

**Symptoms**:
```bash
Error: Configuration file not found: config.yaml
```

**Solutions**:
1. **Create configuration file**:
   ```bash
   # Copy example configuration
   cp config.example.yaml config.yaml

   # Or create minimal config
   cat > config.yaml << EOF
   core:
     storage:
       backend: file
       path: ./registry
   EOF
   ```

2. **Check file permissions**:
   ```bash
   ls -la config.yaml
   chmod 644 config.yaml
   ```

3. **Initialize system**:
   ```bash
   decision-layer init
   ```

#### Problem: Invalid configuration

**Symptoms**:
```bash
Error: Invalid configuration: 'core.storage.backend' must be one of ['file', 'postgresql']
```

**Solutions**:
1. **Validate configuration**:
   ```bash
   decision-layer config validate
   ```

2. **Check YAML syntax**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

3. **Fix configuration values**:
   ```yaml
   core:
     storage:
       backend: file  # Must be 'file' or 'postgresql'
       path: ./registry
   ```

## Performance Issues

### Slow Execution

#### Problem: Function execution is slow

**Symptoms**:
```bash
# Execution time > 1000ms
decision-layer execute loan_approval input.json
# Takes several seconds
```

**Solutions**:
1. **Check system resources**:
   ```bash
   # Monitor CPU and memory
   htop

   # Check disk I/O
   iostat -x 1
   ```

2. **Optimize function code**:
   ```python
   # Use efficient algorithms
   # Avoid unnecessary computations
   # Cache expensive operations
   ```

3. **Configure caching**:
   ```yaml
   plugins:
     caching:
       enabled: true
       plugins:
         - name: memory_cache
           enabled: true
           config:
             max_size: 1000
             ttl: 3600
   ```

4. **Use appropriate storage backend**:
   ```yaml
   core:
     storage:
       backend: postgresql  # Faster than file for large datasets
   ```

### Memory Issues

#### Problem: High memory usage

**Symptoms**:
```bash
# Memory usage > 80%
free -h
```

**Solutions**:
1. **Reduce cache size**:
   ```yaml
   performance:
     cache_size: 500  # Reduce from 1000
   ```

2. **Limit concurrent executions**:
   ```yaml
   performance:
     max_concurrent_executions: 10
   ```

3. **Clean up old traces**:
   ```bash
   # Clear old traces
   decision-layer clear --traces --older-than 30
   ```

4. **Monitor memory usage**:
   ```bash
   # Check memory usage by process
   ps aux --sort=-%mem | head -10
   ```

## Cross-Domain Integration Issues

### LLM Integration Problems

#### Problem: LLM provider not responding

**Symptoms**:
```bash
Error: LLM provider connection failed
```

**Solutions**:
1. **Check API key**:
   ```bash
   echo $DECISION_LAYER_OPENAI_API_KEY
   ```

2. **Test API connection**:
   ```python
   import openai
   openai.api_key = "your-key"
   response = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": "Hello"}]
   )
   ```

3. **Check rate limits**:
   ```bash
   # Wait and retry
   sleep 60
   ```

4. **Use mock provider for testing**:
   ```yaml
   integrations:
     llm:
       provider: mock
   ```

### Ontology Integration Issues

#### Problem: Ontology file not found

**Symptoms**:
```bash
Error: Ontology file not found: ./ontologies/domain.owl
```

**Solutions**:
1. **Create ontology file**:
   ```bash
   mkdir -p ontologies
   # Create or download ontology file
   ```

2. **Check file path**:
   ```yaml
   integrations:
     ontology:
       provider: owl
       config:
         owl:
           file_path: ./ontologies/domain.owl
   ```

3. **Use mock provider**:
   ```yaml
   integrations:
     ontology:
       provider: mock
   ```

### Knowledge Graph Issues

#### Problem: Neo4j connection fails

**Symptoms**:
```bash
Error: Could not connect to Neo4j
```

**Solutions**:
1. **Check Neo4j status**:
   ```bash
   # Check if Neo4j is running
   curl http://localhost:7474
   ```

2. **Verify connection string**:
   ```bash
   # Test connection
   cypher-shell -u neo4j -p password
   ```

3. **Check credentials**:
   ```bash
   echo $DECISION_LAYER_NEO4J_PASSWORD
   ```

4. **Use mock provider**:
   ```yaml
   integrations:
     knowledge_graph:
       provider: mock
   ```

## Security Issues

### Authentication Problems

#### Problem: API key authentication fails

**Symptoms**:
```bash
Error: Authentication failed
```

**Solutions**:
1. **Check API key**:
   ```bash
   echo $DECISION_LAYER_API_KEY
   ```

2. **Verify key format**:
   ```bash
   # Generate new key
   openssl rand -hex 32
   ```

3. **Check request headers**:
   ```bash
   curl -H "X-API-Key: your-key" http://localhost:8000/health
   ```

4. **Disable authentication for development**:
   ```yaml
   security:
     enable_auth: false
   ```

### Rate Limiting Issues

#### Problem: Rate limit exceeded

**Symptoms**:
```bash
Error: Rate limit exceeded
```

**Solutions**:
1. **Increase rate limit**:
   ```yaml
   security:
     rate_limiting:
       requests_per_minute: 1000  # Increase from 100
   ```

2. **Disable rate limiting for development**:
   ```yaml
   security:
     rate_limiting:
       enabled: false
   ```

3. **Implement client-side throttling**:
   ```python
   import time
   import requests

   def throttled_request(url, headers, delay=0.1):
       time.sleep(delay)
       return requests.get(url, headers=headers)
   ```

## Logging and Debugging

### Enable Debug Mode

```bash
# Set debug environment variable
export DECISION_LAYER_DEBUG=true

# Or set in configuration
echo "debug: true" >> config.yaml
```

### View Logs

```bash
# View application logs
tail -f logs/decision_layer.log

# View system logs
journalctl -u decision-layer -f

# View Docker logs
docker logs -f decision-layer
```

### Debug Configuration

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test configuration
from decision_layer.config import ConfigManager
config = ConfigManager()
print(config.get('core.storage.backend'))
```

## Getting Help

### Collect Debug Information

```bash
# Create debug report
decision-layer debug report > debug_report.txt

# Include system information
uname -a >> debug_report.txt
python --version >> debug_report.txt
pip list >> debug_report.txt
```

### Common Support Channels

1. **Documentation**: Check the [docs/](docs/) directory
2. **Examples**: Review the [examples/](../examples/) directory
3. **GitHub Issues**: Report bugs on [GitHub Issues](https://github.com/data-riot/decision-layer/issues)
4. **Discussions**: Join [GitHub Discussions](https://github.com/data-riot/decision-layer/issues)

### Reporting Issues

When reporting issues, include:

1. **Error message** - Complete error text
2. **Steps to reproduce** - Detailed steps
3. **Environment** - OS, Python version, dependencies
4. **Configuration** - Relevant config files
5. **Logs** - Application and system logs
6. **Expected behavior** - What should happen
7. **Actual behavior** - What actually happens

## Prevention

### Best Practices

1. **Use virtual environments** - Isolate dependencies
2. **Version control** - Track configuration changes
3. **Regular backups** - Backup data and configuration
4. **Monitoring** - Set up health checks and alerts
5. **Testing** - Test functions before deployment
6. **Documentation** - Document custom configurations

### Maintenance

1. **Regular updates** - Keep dependencies updated
2. **Log rotation** - Prevent log files from growing too large
3. **Data cleanup** - Remove old traces and data
4. **Performance monitoring** - Monitor system performance
5. **Security updates** - Keep security patches current

## Next Steps

- **Read the [Configuration Guide](configuration.md)** for detailed configuration options
- **Check the [Deployment Guide](deployment.md)** for deployment troubleshooting
- **Review the [API Reference](api.md)** for API-specific issues
- **Explore the [Examples](../examples/)** for working solutions
