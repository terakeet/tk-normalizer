SHELL := /bin/bash
.PHONY: help install test lint format clean build publish help-publish

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install all dependencies
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with coverage
	pytest tests/ -v --cov=tk_normalizer --cov-report=term --cov-report=html

test-unit: ## Run only unit tests
	pytest tests/ -v -m unit

test-integration: ## Run only integration tests
	pytest tests/ -v -m integration

test-watch: ## Run tests in watch mode (requires pytest-watch)
	pip install pytest-watch
	ptw tests/ -- -v

lint: ## Run all checks (lint + format check)
	ruff check .
	ruff format --check .

format: ## Format code automatically
	ruff format .
	ruff check . --fix

clean: ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/

build: clean ## Build distribution packages
	python -m build

publish: ## Publish to PyPI
	@echo "⚠️  Warning: Publishing to PyPI!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		twine upload dist/*; \
	fi

publish-test: ## Publish to TestPyPI
	twine upload --repository testpypi dist/*

help-publish: ## Show help for publishing
	@echo "To publish to PyPI:"
	@echo "  1. Update version in pyproject.toml"
	@echo "  2. Run 'make build' to create distribution packages"
	@echo "  3. Run 'make publish-test' to test on TestPyPI (optional)"
	@echo "  4. Run 'make publish' to publish to PyPI"

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

setup: install ## Complete local development setup
	@echo "✅ Setup complete!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code style"
	@echo "Run 'make build' to build distribution packages"

venv: ## Create virtual environment
	python3.11 -m venv .venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

upgrade-deps: ## Upgrade all dependencies to latest versions
	pip install --upgrade pip
	pip list --outdated
	@echo "Review outdated packages above. Update pyproject.toml manually."

check: lint test ## Run all checks (lint + test)
	@echo "✅ All checks passed!"
