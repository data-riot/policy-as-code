# Decision Layer Development Guide

This guide covers the development setup, tools, and best practices for contributing to the Decision Layer project.

## 🚀 Quick Start

### Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Run the automated setup script
./scripts/dev-setup.sh
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev,test,docs,monitoring]"

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

## 🛠️ Development Tools

### Code Quality Tools

The project uses several tools to maintain code quality:

- **Black**: Code formatting (includes import sorting)
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **safety**: Dependency security

### Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit:

```bash
# Install hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### VS Code Configuration

The project includes VS Code settings for optimal development experience:

- **Python interpreter**: Automatically uses the virtual environment
- **Format on save**: Automatically formats code with Black
- **Linting**: Real-time linting with flake8
- **Type checking**: Real-time type checking with mypy
- **Testing**: Integrated pytest support

## 📋 Development Commands

### Using Make (Recommended)

The project includes a comprehensive Makefile with common development tasks:

```bash
# Show all available commands
make help

# Common development tasks
make dev-setup      # Complete development setup
make dev-check      # Run all checks (lint, type-check, test)
make dev-format     # Format all code
make test           # Run all tests
make lint           # Run all linting checks
make format         # Format code
make type-check     # Run type checking
make security-check # Run security checks
make coverage       # Run tests with coverage
make serve-dev      # Start development server
make serve-web      # Start web interface
make clean          # Clean up generated files
```

### Direct Commands

```bash
# Testing
python -m pytest tests/ -v                    # Run all tests
python -m pytest tests/unit/ -v               # Run unit tests only
python -m pytest tests/ --cov=decision_layer  # Run with coverage

# Code Quality
black decision_layer tests examples           # Format code
black decision_layer tests examples           # Format code
flake8 decision_layer tests examples          # Lint code
mypy decision_layer                           # Type check
bandit -r decision_layer                      # Security scan

# Development Servers
uvicorn decision_layer.api:app --reload      # API server
streamlit run streamlit_app.py               # Web interface
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── conftest.py    # Test configuration
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
make coverage
make coverage-html  # Generate HTML report

# Run tests in watch mode
make test-watch
```

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for local development:

```bash
# Development environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# API Configuration
API_HOST=localhost
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-change-in-production
ENABLE_AUTH=false

# Storage
STORAGE_BACKEND=file
STORAGE_PATH=./registry

# Tracing
TRACE_DIR=./traces
TRACE_LEVEL=INFO
```

### Configuration Files

- **pyproject.toml**: Project configuration and tool settings
- **pytest.ini**: Test configuration
- **.pre-commit-config.yaml**: Pre-commit hooks configuration
- **.vscode/settings.json**: VS Code settings
- **Makefile**: Development task automation

## 📚 Documentation

### Building Documentation

```bash
# Build documentation
make docs

# Serve documentation locally
make docs-serve
```

### Documentation Structure

```
docs/
├── README.md           # Documentation index
├── architecture.md     # System architecture
├── installation.md     # Installation guide
├── quickstart.md       # Quick start tutorial
├── api.md             # API reference
├── cli.md             # CLI reference
├── web-interface.md   # Web interface guide
├── configuration.md   # Configuration guide
├── deployment.md      # Deployment guide
└── troubleshooting.md # Troubleshooting guide
```

## 🔒 Security

### Security Checks

```bash
# Run security scan
make security-check

# Check dependencies for vulnerabilities
safety check

# Scan code for security issues
bandit -r decision_layer
```

### Security Best Practices

1. **Never commit secrets**: Use environment variables for sensitive data
2. **Keep dependencies updated**: Regularly update dependencies
3. **Use security scanning**: Run bandit and safety checks
4. **Validate inputs**: Always validate and sanitize inputs
5. **Use HTTPS**: Use HTTPS in production

## 🚀 Deployment

### Docker

```bash
# Build Docker image
make docker-build

# Run Docker container
make docker-run

# Run tests in Docker
make docker-test
```

### Production Checklist

Before deploying to production:

```bash
# Run complete release preparation
make release
```

This includes:
- Running all tests
- Running linting checks
- Running type checking
- Running security checks
- Building the package

## 🐛 Debugging

### Debug Mode

```bash
# Start with debug logging
make debug

# View logs
make logs
```

### Common Issues

#### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall package
pip install -e .
```

#### Test Failures
```bash
# Run tests with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/test_specific.py::test_function -v

# Run with coverage to see what's missing
pytest tests/ --cov=decision_layer --cov-report=term-missing
```

#### Linting Issues
```bash
# Auto-fix formatting issues
make format

# Check specific files
flake8 decision_layer/specific_file.py

# Ignore specific errors
# noqa: E501  # Line too long
```

## 📊 Monitoring

### Metrics

The project includes monitoring capabilities:

```bash
# Enable metrics
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Logging

```bash
# Set log level
LOG_LEVEL=DEBUG

# View logs
tail -f logs/decision-layer.log
```

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run development checks**
   ```bash
   make dev-check
   ```
5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a pull request**

### Commit Message Format

Use conventional commit messages:

```
type(scope): description

feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: maintenance tasks
```

### Code Review Checklist

Before submitting a pull request:

- [ ] All tests pass
- [ ] Code is formatted (Black)
- [ ] Code is formatted (Black)
- [ ] No linting errors (flake8)
- [ ] Type checking passes (mypy)
- [ ] Security checks pass (bandit)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

## 🆘 Getting Help

### Resources

- **Documentation**: [docs/](docs/)
- **API Reference**: [docs/api.md](docs/api.md)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/data-riot/decision-layer/issues)

### Common Commands Reference

```bash
# Development setup
./scripts/dev-setup.sh

# Quick development workflow
make dev

# Run all checks
make dev-check

# Format code
make format

# Run tests
make test

# Start development server
make serve-dev

# Start web interface
make serve-web

# Clean up
make clean
```

### Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues and solutions.

## 📈 Performance

### Profiling

```bash
# Run performance profiling
make profile

# Run benchmarks
make benchmark
```

### Optimization Tips

1. **Use async/await**: For I/O operations
2. **Profile your code**: Identify bottlenecks
3. **Use caching**: For expensive operations
4. **Optimize database queries**: Use proper indexing
5. **Monitor memory usage**: Avoid memory leaks

## 🔄 Continuous Integration

The project uses GitHub Actions for CI/CD:

- **Tests**: Run on multiple Python versions
- **Linting**: Check code quality
- **Type checking**: Verify type annotations
- **Security**: Scan for vulnerabilities
- **Documentation**: Build and deploy docs

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
