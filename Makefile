# Makefile for Personal RSS Updater development

.PHONY: help install dev-install format lint test test-cov clean pre-commit setup-hooks act-list act-init act-daily act-setup

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package and dependencies
	uv sync

dev-install:  ## Install package with development dependencies
	uv sync --group dev

format:  ## Format code with black
	uv run black src/ tests/

lint:  ## Lint code with ruff and mypy
	uv run ruff check src/ tests/ --fix
	uv run mypy src/ --ignore-missing-imports

test:  ## Run tests
	uv run python -m pytest --tb=short -v

test-cov:  ## Run tests with coverage
	uv run python -m pytest --cov=rss_updater --cov-report=html --cov-report=term-missing

test-feeds:  ## Run only RSS feed tests
	uv run python -m pytest tests/test_feeds.py -v

clean:  ## Clean up build artifacts
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

setup-hooks:  ## Install pre-commit hooks
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

pre-commit:  ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

pre-commit-update:  ## Update pre-commit hooks
	uv run pre-commit autoupdate

# Quality checks - run before committing
quality: format lint test  ## Run all quality checks (format, lint, test)

# CI simulation - what will run on GitHub Actions
ci: lint test-cov  ## Run CI checks locally

# GitHub Actions local testing with act
act-setup:  ## Set up secrets file for act testing
	@if [ ! -f .env.secrets ]; then \
		echo "Creating .env.secrets from template..."; \
		cp .env.secrets.example .env.secrets; \
		echo "Please edit .env.secrets with your actual values"; \
	else \
		echo ".env.secrets already exists"; \
	fi

act-list:  ## List available workflows
	act -l

act-init:  ## Test initialize-rss workflow locally
	act workflow_dispatch -W .github/workflows/initialize-rss.yml

act-daily:  ## Test daily-rss-check workflow locally
	act workflow_dispatch -W .github/workflows/daily-rss-check.yml

act-dry:  ## Dry run of workflows (no execution)
	act -n
