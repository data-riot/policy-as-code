# Installation Guide

This guide covers all installation options for the Decision Layer framework.

## Prerequisites

- **Python 3.8+** - The framework requires Python 3.8 or higher
- **Git** - For cloning the repository
- **pip** - Python package installer

## Installation Options

### Option 1: Quick Install (Recommended)

For most users, this is the fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 2: Virtual Environment (Recommended for Development)

For development or to avoid conflicts with other Python packages:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 3: Docker Installation

For containerized deployment:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t decision-layer .
docker run -p 8000:8000 -p 8501:8501 decision-layer
```

### Option 4: Production Installation

For production environments:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Copy environment configuration
cp env.example .env

# Edit configuration (see Configuration section below)
nano .env

# Install production dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Initialize the system
decision-layer init
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/decision_layer

# Security
DECISION_LAYER_API_KEY=your-secret-api-key
SECRET_KEY=your-secret-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/decision_layer.log

# Storage
STORAGE_BACKEND=file  # or postgresql
STORAGE_PATH=./data

# Cross-Domain Integration
LLM_PROVIDER=mock  # or openai, anthropic
ONTOLOGY_PROVIDER=mock  # or owl, neo4j
KG_PROVIDER=mock  # or neo4j, amazon_neptune
```

### Configuration File

The main configuration is in `config.yaml`:

```yaml
# Core Configuration
core:
  storage_backend: file
  trace_dir: ./traces
  max_input_size: 1048576  # 1MB

# Plugin Configuration
plugins:
  validation:
    enabled: true
  tracing:
    enabled: true
    path: ./traces
  caching:
    enabled: true

# Security Configuration
security:
  enable_rate_limiting: true
  enable_input_sanitization: true
  enable_trace_sanitization: true
  max_input_size: 1048576
  rate_limit_requests: 100
  rate_limit_window: 60

# Cross-Domain Integration
integrations:
  llm:
    provider: mock
    config: {}
  ontology:
    provider: mock
    config: {}
  knowledge_graph:
    provider: mock
    config: {}
```

## Verification

After installation, verify that everything is working:

### 1. Check Installation

```bash
# Test package import
python -c "import decision_layer; print('✅ Decision Layer imported successfully')"

# Check version
python -c "import decision_layer; print(f'Version: {decision_layer.__version__}')"
```

### 2. Test CLI

```bash
# Check CLI installation
decision-layer --help

# Initialize the system
decision-layer init
```

### 3. Test Web Interface

```bash
# Start the web interface
python run_ui.py

# Open http://localhost:8501 in your browser
```

### 4. Test API

```bash
# Start the API server
python run_api.py

# Test API health
curl http://localhost:8000/health
```

## Development Setup

For developers who want to contribute to the project:

### 1. Install Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Development Tools

The project includes several development tools:

- **Black**: Code formatting (includes import sorting)
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### 3. Run Development Tools

```bash
# Format code
black decision_layer tests

# Sort imports
black decision_layer tests

# Lint code
flake8 decision_layer tests

# Type check
mypy decision_layer

# Run tests
pytest tests/
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'decision_layer'`

**Solution**: Make sure you've installed the package in development mode:
```bash
pip install -e .
```

#### 2. Permission Errors

**Problem**: Permission denied when creating directories

**Solution**: Check file permissions and ensure you have write access to the installation directory.

#### 3. Port Conflicts

**Problem**: Port 8000 or 8501 already in use

**Solution**: Change ports in configuration or stop conflicting services:
```bash
# Find processes using ports
lsof -i :8000
lsof -i :8501

# Kill processes if needed
kill -9 <PID>
```

#### 4. Database Connection Issues

**Problem**: Cannot connect to PostgreSQL

**Solution**:
- Ensure PostgreSQL is running
- Check connection string in `.env`
- Verify database exists and user has permissions

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look in `logs/` directory for error messages
2. **Review configuration**: Ensure all settings in `config.yaml` and `.env` are correct
3. **Search issues**: Check existing GitHub issues for similar problems
4. **Create issue**: Open a new GitHub issue with detailed error information

## Next Steps

After successful installation:

1. **Read the [Quick Start Guide](quickstart.md)** for your first decision function
2. **Explore the [Examples](../examples/)** to see working implementations
3. **Check the [Architecture Documentation](architecture.md)** to understand the system design
4. **Review the [API Documentation](api.md)** for programmatic access

## Support

For additional support:

- **Documentation**: Check the [docs/](docs/) directory
- **Examples**: Review the [examples/](../examples/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/data-riot/decision-layer/issues)
- **Discussions**: Join the [GitHub Discussions](https://github.com/data-riot/decision-layer/issues)
