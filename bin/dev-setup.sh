#!/bin/bash

# Decision Layer Development Setup Script
# This script sets up a complete development environment

set -e  # Exit on any error

echo "🚀 Setting up Decision Layer Development Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is available
check_python() {
    print_status "Checking Python version..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.8+"
        exit 1
    fi
}

# Check if pip is available
check_pip() {
    print_status "Checking pip..."

    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install pip"
        exit 1
    fi

    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi

    print_success "pip found"
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi

    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."

    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi

    print_success "Virtual environment activated"
}

# Upgrade pip and install build tools
upgrade_pip() {
    print_status "Upgrading pip and installing build tools..."

    $PIP_CMD install --upgrade pip setuptools wheel
    print_success "pip upgraded"
}

# Install development dependencies
install_deps() {
    print_status "Installing development dependencies..."

    # Install the package in editable mode with dev dependencies
    $PIP_CMD install -e ".[dev,test,docs,monitoring]"

    print_success "Development dependencies installed"
}

# Install pre-commit hooks
install_precommit() {
    print_status "Installing pre-commit hooks..."

    pre-commit install
    pre-commit install --hook-type commit-msg

    print_success "Pre-commit hooks installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."

    mkdir -p registry traces data logs docs/_build tests/unit tests/integration tests/e2e
    print_success "Directories created"
}

# Create configuration files
create_configs() {
    print_status "Creating configuration files..."

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Decision Layer Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# API Configuration
API_HOST=localhost
API_PORT=8000
API_WORKERS=1

# Security
SECRET_KEY=changeme-secret-key-in-production
ENABLE_AUTH=false

# Storage
STORAGE_BACKEND=file
STORAGE_PATH=./registry

# Tracing
TRACE_DIR=./traces
TRACE_LEVEL=INFO

# Database (if using PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/policy_as_code

# Redis (if using Redis)
REDIS_URL=redis://localhost:6379/0

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Cross-domain Integration
LLM_PROVIDER=mock
ONTOLOGY_PROVIDER=mock
KG_PROVIDER=mock
EOF
        print_success ".env file created"
    else
        print_warning ".env file already exists"
    fi

    # Create pytest.ini if it doesn't exist
    if [ ! -f "pytest.ini" ]; then
        cat > pytest.ini << EOF
[tool:pytest]
minversion = 7.0
addopts =
    -ra
    --strict-markers
    --strict-config
    --cov=policy_as_code
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
    --durations=10
    --tb=short
    --maxfail=3
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    e2e: marks tests as end-to-end tests
    api: marks tests as API tests
    cli: marks tests as CLI tests
    web: marks tests as web interface tests
EOF
        print_success "pytest.ini created"
    else
        print_warning "pytest.ini already exists"
    fi
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."

    if $PYTHON_CMD -m pytest tests/ -v --tb=short; then
        print_success "Tests passed"
    else
        print_warning "Some tests failed (this is expected for initial setup)"
    fi
}

# Run code quality checks
run_quality_checks() {
    print_status "Running code quality checks..."

    # Format code
    $PYTHON_CMD -m black policy_as_code tests examples --check || {
        print_warning "Code formatting issues found. Run 'black policy_as_code tests examples' to fix"
    }

    # Sort imports
    $PYTHON_CMD -m isort policy_as_code tests examples --check-only || {
        print_warning "Import sorting issues found. Run 'isort policy_as_code tests examples' to fix"
    }

    # Lint code
    $PYTHON_CMD -m flake8 policy_as_code tests examples || {
        print_warning "Linting issues found"
    }

    # Type checking
    $PYTHON_CMD -m mypy policy_as_code || {
        print_warning "Type checking issues found"
    }

    print_success "Code quality checks completed"
}

# Create development scripts
create_dev_scripts() {
    print_status "Creating development scripts..."

    mkdir -p scripts

    # Create run-dev.sh
    cat > scripts/run-dev.sh << 'EOF'
#!/bin/bash
# Development server runner

set -e

echo "🚀 Starting Decision Layer Development Server"
echo "============================================="

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the API server
echo "Starting API server on http://localhost:${API_PORT:-8000}"
echo "API documentation: http://localhost:${API_PORT:-8000}/docs"
echo "Press Ctrl+C to stop"

python -m uvicorn policy_as_code.api:app --host ${API_HOST:-localhost} --port ${API_PORT:-8000} --reload
EOF

    # Create run-web.sh
    cat > scripts/run-web.sh << 'EOF'
#!/bin/bash
# Web interface runner

set -e

echo "🌐 Starting Decision Layer Web Interface"
echo "========================================"

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the API server instead (web interface not implemented)
echo "Starting API server on http://localhost:8000"
echo "Press Ctrl+C to stop"

python run_api.py
EOF

    # Create test-all.sh
    cat > scripts/test-all.sh << 'EOF'
#!/bin/bash
# Comprehensive test runner

set -e

echo "🧪 Running Comprehensive Tests"
echo "=============================="

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Run all tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

echo "Running integration tests..."
python -m pytest tests/integration/ -v

echo "Running end-to-end tests..."
python -m pytest tests/e2e/ -v

echo "Running with coverage..."
python -m pytest tests/ --cov=policy_as_code --cov-report=html --cov-report=term-missing

echo "✅ All tests completed!"
EOF

    # Make scripts executable
    chmod +x scripts/*.sh

    print_success "Development scripts created"
}

# Display setup completion
show_completion() {
    echo ""
    echo "🎉 Development Environment Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate  # Linux/Mac"
    echo "   venv\\Scripts\\activate     # Windows"
    echo ""
    echo "2. Start the development server:"
    echo "   ./scripts/run-dev.sh"
    echo ""
    echo "3. Start the web interface:"
    echo "   ./scripts/run-web.sh"
    echo ""
    echo "4. Run tests:"
    echo "   ./scripts/test-all.sh"
    echo ""
    echo "5. Format code:"
    echo "   black policy_as_code tests examples"
    echo "   isort policy_as_code tests examples"
    echo ""
    echo "6. Check code quality:"
    echo "   flake8 policy_as_code tests examples"
    echo "   mypy policy_as_code"
    echo ""
    echo "Useful commands:"
    echo "  python -m pytest tests/ -v          # Run tests"
    echo "  python -m black .                   # Format code"
    echo "  python -m isort .                   # Sort imports"
    echo "  python -m flake8 .                  # Lint code"
    echo "  python -m mypy policy_as_code       # Type check"
    echo "  pre-commit run --all-files          # Run all pre-commit hooks"
    echo ""
    echo "Documentation:"
    echo "  API docs: http://localhost:8000/docs"
    echo "  Web interface: http://localhost:8501"
    echo ""
}

# Main execution
main() {
    check_python
    check_pip
    create_venv
    activate_venv
    upgrade_pip
    install_deps
    install_precommit
    create_directories
    create_configs
    run_tests
    run_quality_checks
    create_dev_scripts
    show_completion
}

# Run main function
main "$@"
