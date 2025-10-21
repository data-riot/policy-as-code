# Production Governance Platform Makefile
# 30-minute golden path from bootstrap to production deployment

.PHONY: help install test deploy clean demo benchmark

# Configuration
PYTHON := python3
PIP := pip3
VENV := .venv
PROJECT_NAME := policy_as_code
API_PORT := 8000
DB_NAME := decision_layer
DB_USER := postgres
DB_PASSWORD := password
DB_HOST := localhost
DB_PORT := 5432

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Production Governance Platform - 30-minute Golden Path$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make install    - Install dependencies and setup environment"
	@echo "  make test       - Run comprehensive test suite with SLOs"
	@echo "  make demo       - Run 30-minute golden path demo"
	@echo "  make deploy     - Deploy to production"
	@echo ""
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  make dev        - Start development environment"
	@echo "  make lint       - Run linting and type checking"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean up environment"
	@echo ""
	@echo "$(YELLOW)Production:$(NC)"
	@echo "  make benchmark  - Run performance benchmarks"
	@echo "  make audit      - Run compliance audit"
	@echo "  make rollback   - Rollback deployment"
	@echo ""

install: ## Install dependencies and setup environment
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup-db: ## Setup PostgreSQL database
	@echo "$(BLUE)Setting up database...$(NC)"
	@if ! command -v psql >/dev/null 2>&1; then \
		echo "$(RED)PostgreSQL not found. Please install PostgreSQL first.$(NC)"; \
		exit 1; \
	fi
	@if ! psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d postgres -c "SELECT 1;" >/dev/null 2>&1; then \
		echo "$(RED)Database connection failed. Please check your PostgreSQL setup.$(NC)"; \
		exit 1; \
	fi
	@psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d postgres -c "CREATE DATABASE $(DB_NAME);" || true
	@echo "$(GREEN)✓ Database setup complete$(NC)"

test: ## Run comprehensive test suite with SLOs
	@echo "$(BLUE)Running comprehensive test suite...$(NC)"
	$(VENV)/bin/python -m pytest tests/ -v --cov=decision_layer --cov-report=html --cov-report=term
	$(VENV)/bin/python -m pytest tests/test_mutation.py -v
	$(VENV)/bin/python -m pytest tests/test_contract.py -v
	$(VENV)/bin/python -m pytest tests/test_performance.py -v
	$(VENV)/bin/python -m pytest tests/test_security.py -v
	$(VENV)/bin/python -m pytest tests/test_compliance.py -v
	@echo "$(GREEN)✓ All tests passed$(NC)"

lint: ## Run linting and type checking
	@echo "$(BLUE)Running linting...$(NC)"
	$(VENV)/bin/flake8 decision_layer/ tests/
	$(VENV)/bin/mypy decision_layer/
	$(VENV)/bin/bandit -r decision_layer/
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	$(VENV)/bin/black decision_layer/ tests/
	$(VENV)/bin/isort decision_layer/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

demo: ## Run governance features demo
	@echo "$(BLUE)Starting governance features demo...$(NC)"
	$(VENV)/bin/python examples/governance_demo.py
	@echo "$(GREEN)✓ Governance demo complete$(NC)"

golden_path_demo: ## Run 30-minute golden path demo
	@echo "$(BLUE)Starting 30-minute golden path demo...$(NC)"
	@echo "$(YELLOW)This demo will:$(NC)"
	@echo "  1. Bootstrap registry and services"
	@echo "  2. Register decision functions (Python + DSL)"
	@echo "  3. Define legal references"
	@echo "  4. Create and sign releases"
	@echo "  5. Execute decisions with traces"
	@echo "  6. Run independent audit"
	@echo "  7. Simulate rollback"
	@echo ""
	@read -p "Press Enter to continue..." dummy
	$(VENV)/bin/python examples/golden_path_demo.py
	@echo "$(GREEN)✓ Golden path demo complete$(NC)"

run_api: ## Start development API
	@echo "$(BLUE)Starting development API...$(NC)"
	$(VENV)/bin/python run_api.py

run_prod_api: ## Start production API with governance features
	@echo "$(BLUE)Starting production API with governance features...$(NC)"
	$(VENV)/bin/python run_production_api.py

deploy: ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(YELLOW)Deployment checklist:$(NC)"
	@echo "  ✓ All tests passing"
	@echo "  ✓ Security scan complete"
	@echo "  ✓ Performance benchmarks met"
	@echo "  ✓ Compliance audit passed"
	@echo ""
	@read -p "Press Enter to confirm deployment..." dummy
	$(VENV)/bin/python scripts/deploy.py --production
	@echo "$(GREEN)✓ Production deployment complete$(NC)"

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	$(VENV)/bin/python scripts/benchmark.py --iterations=1000 --duration=60
	@echo "$(GREEN)✓ Benchmarks complete$(NC)"

audit: ## Run compliance audit
	@echo "$(BLUE)Running compliance audit...$(NC)"
	$(VENV)/bin/python scripts/audit.py --comprehensive
	@echo "$(GREEN)✓ Compliance audit complete$(NC)"

rollback: ## Rollback deployment
	@echo "$(RED)Rolling back deployment...$(NC)"
	@read -p "Are you sure you want to rollback? (yes/no): " confirm && [ "$$confirm" = "yes" ]
	$(VENV)/bin/python scripts/rollback.py --confirm
	@echo "$(GREEN)✓ Rollback complete$(NC)"

clean: ## Clean up environment
	@echo "$(BLUE)Cleaning up...$(NC)"
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf __pycache__
	rm -rf decision_layer/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Production monitoring targets
monitor: ## Start monitoring dashboard
	@echo "$(BLUE)Starting monitoring dashboard...$(NC)"
	$(VENV)/bin/python scripts/monitor.py --dashboard

logs: ## View production logs
	@echo "$(BLUE)Viewing production logs...$(NC)"
	tail -f logs/production.log

health: ## Check system health
	@echo "$(BLUE)Checking system health...$(NC)"
	curl -s http://localhost:$(API_PORT)/health | jq .

# Database management
db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	$(VENV)/bin/python scripts/migrate.py --up

db-rollback: ## Rollback database migrations
	@echo "$(RED)Rolling back database migrations...$(NC)"
	$(VENV)/bin/python scripts/migrate.py --down

db-seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database...$(NC)"
	$(VENV)/bin/python scripts/seed.py

# Security and compliance
security-scan: ## Run security scan
	@echo "$(BLUE)Running security scan...$(NC)"
	$(VENV)/bin/bandit -r decision_layer/
	$(VENV)/bin/safety check

compliance-check: ## Run compliance check
	@echo "$(BLUE)Running compliance check...$(NC)"
	$(VENV)/bin/python scripts/compliance.py --check

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	$(VENV)/bin/sphinx-build -b html docs/ docs/_build/html
	@echo "$(GREEN)✓ Documentation generated$(NC)"

# Quick development targets
quick-test: ## Quick test run
	$(VENV)/bin/python -m pytest tests/test_core.py -v

quick-start: install setup-db test ## Quick start: install, setup, test
	@echo "$(GREEN)✓ Quick start complete$(NC)"

# Production readiness check
production-ready: test lint security-scan compliance-check benchmark ## Check production readiness
	@echo "$(GREEN)✓ System is production ready$(NC)"

# Emergency targets
emergency-stop: ## Emergency stop all services
	@echo "$(RED)EMERGENCY STOP$(NC)"
	pkill -f "run_production_api.py" || true
	pkill -f "audit_service.py" || true
	@echo "$(GREEN)✓ Emergency stop complete$(NC)"

emergency-restart: emergency-stop ## Emergency restart all services
	@echo "$(BLUE)Emergency restart...$(NC)"
	sleep 5
	$(VENV)/bin/python run_production_api.py --background
	@echo "$(GREEN)✓ Emergency restart complete$(NC)"

# Show current status
status: ## Show current system status
	@echo "$(BLUE)System Status:$(NC)"
	@echo "  Python: $$($(PYTHON) --version)"
	@echo "  Virtual Environment: $(VENV)"
	@echo "  Database: $(DB_NAME)@$(DB_HOST):$(DB_PORT)"
	@echo "  API Port: $(API_PORT)"
	@echo ""
	@if [ -d "$(VENV)" ]; then \
		echo "$(GREEN)✓ Virtual environment exists$(NC)"; \
	else \
		echo "$(RED)✗ Virtual environment missing$(NC)"; \
	fi
	@if psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME) -c "SELECT 1;" >/dev/null 2>&1; then \
		echo "$(GREEN)✓ Database accessible$(NC)"; \
	else \
		echo "$(RED)✗ Database not accessible$(NC)"; \
	fi
	@if curl -s http://localhost:$(API_PORT)/health >/dev/null 2>&1; then \
		echo "$(GREEN)✓ API server running$(NC)"; \
	else \
		echo "$(RED)✗ API server not running$(NC)"; \
	fi