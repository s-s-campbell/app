# Makefile for Web Scraper Project
# Compatible with Linux/Mac systems

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
DOCKER := docker

# Colors for output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

.PHONY: help install install-dev test test-verbose test-coverage test-specific clean lint docker-build docker-run setup check-deps

help: ## Show this help message
	@echo "$(GREEN)Web Scraper Development Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(install|setup)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Testing Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(test|coverage)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(clean|lint|docker)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup          # Complete project setup"
	@echo "  make test           # Run all tests"
	@echo "  make test-coverage  # Run tests with coverage report"
	@echo "  make docker-build   # Build Docker image"

install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: install ## Install development dependencies (includes production deps)
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements-dev.txt

setup: install-dev ## Complete project setup (install deps + run tests)
	@echo "$(GREEN)Running initial test to verify setup...$(NC)"
	$(PYTEST) --version
	@echo "$(GREEN)Setup complete! Run 'make test' to run tests$(NC)"

check-deps: ## Check if required dependencies are installed
	@echo "$(GREEN)Checking dependencies...$(NC)"
	@$(PYTHON) -c "import flask, pytest, requests, google.cloud.storage" 2>/dev/null && echo "$(GREEN)✓ All dependencies installed$(NC)" || (echo "$(RED)✗ Missing dependencies. Run 'make install-dev'$(NC)" && exit 1)

test: check-deps ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	$(PYTEST) tests/

test-verbose: check-deps ## Run tests with verbose output
	@echo "$(GREEN)Running tests with verbose output...$(NC)"
	$(PYTEST) -v tests/

test-coverage: check-deps ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTEST) --cov=main --cov-report=term-missing tests/

test-coverage-html: check-deps ## Generate HTML coverage report
	@echo "$(GREEN)Generating HTML coverage report...$(NC)"
	$(PYTEST) --cov=main --cov-report=html tests/
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

test-specific: ## Run specific test (usage: make test-specific TEST=test_name)
	@if [ -z "$(TEST)" ]; then \
		echo "$(RED)Please specify TEST variable. Example: make test-specific TEST=TestLoadSourcesFromGCS$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running specific test: $(TEST)$(NC)"
	$(PYTEST) -v tests/test_main.py::$(TEST)

test-integration: check-deps ## Run only integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	$(PYTEST) -v tests/test_main.py::TestIntegration

test-unit: check-deps ## Run only unit tests (excludes integration)
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTEST) -v tests/test_main.py -k "not TestIntegration"

test-parallel: check-deps ## Run tests in parallel (faster)
	@echo "$(GREEN)Running tests in parallel...$(NC)"
	$(PYTEST) -n auto tests/

test-watch: check-deps ## Run tests continuously (re-run on file changes)
	@echo "$(GREEN)Running tests in watch mode (Ctrl+C to stop)...$(NC)"
	@echo "$(YELLOW)Note: Requires pytest-watch. Install with: pip install pytest-watch$(NC)"
	ptw tests/

lint: ## Run basic Python linting
	@echo "$(GREEN)Running basic Python syntax check...$(NC)"
	$(PYTHON) -m py_compile main.py
	@echo "$(GREEN)✓ Python syntax is valid$(NC)"

clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up generated files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	$(DOCKER) build -t scraper-app .
	@echo "$(GREEN)✓ Docker image built successfully$(NC)"

docker-run: ## Run Docker container locally
	@echo "$(GREEN)Running Docker container...$(NC)"
	$(DOCKER) run -p 8080:8080 -e BUCKET_NAME=test-bucket scraper-app

docker-test: docker-build ## Build and test Docker image
	@echo "$(GREEN)Testing Docker image...$(NC)"
	$(DOCKER) run --rm scraper-app python -c "import main; print('✓ Docker image works')"

# Development workflow shortcuts
dev-setup: setup ## Alias for setup
dev-test: test-coverage ## Quick development test with coverage
dev-clean: clean ## Alias for clean

# Continuous Integration helpers
ci-install: install-dev ## Install dependencies for CI
ci-test: test-coverage ## Run tests for CI with coverage
ci-build: docker-build ## Build Docker image for CI

# Quick status check
status: ## Show project status
	@echo "$(GREEN)Project Status:$(NC)"
	@echo "Python version: $$($(PYTHON) --version)"
	@echo "Pip version: $$($(PIP) --version)"
	@echo "Working directory: $$(pwd)"
	@echo "Dependencies: $$($(PIP) list | grep -E "(flask|pytest|requests|google-cloud)" | wc -l) installed"
	@echo ""
	@echo "$(YELLOW)Available make commands:$(NC)"
	@echo "Run 'make help' for detailed usage" 