# RedForge CLI Makefile
# Reference: cid-roadmap-v1 Sprint S-1

.PHONY: help install build test lint clean docker-build docker-run dev

# Default target
help: ## Show this help message
	@echo "RedForge CLI - Developer Commands"
	@echo "Reference: cid-roadmap-v1 Sprint S-1"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	poetry install --with dev
	poetry run pre-commit install

build: ## Build the package
	poetry build

test: ## Run tests
	poetry run pytest tests/ -v --cov=redforge --cov-report=html

test-fast: ## Run fast tests only
	poetry run pytest tests/ -v -m "not slow"

lint: ## Run linting and formatting
	poetry run black redforge/ tests/
	poetry run isort redforge/ tests/
	poetry run flake8 redforge/ tests/
	poetry run mypy redforge/

lint-check: ## Check formatting without making changes
	poetry run black --check redforge/ tests/
	poetry run isort --check-only redforge/ tests/
	poetry run flake8 redforge/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Docker targets
docker-build: ## Build Docker image
	docker build -t redforge/cli:latest .

docker-build-dev: ## Build development Docker image
	docker build --target builder -t redforge/cli:dev .

docker-run: ## Run CLI in Docker container
	docker run --rm \
		-e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-v $(PWD)/reports:/app/reports \
		redforge/cli:latest $(ARGS)

docker-scan: ## Run scan command in Docker
	docker run --rm \
		-e OPENAI_API_KEY=${OPENAI_API_KEY} \
		-v $(PWD)/reports:/app/reports \
		redforge/cli:latest scan $(TARGET) $(ARGS)

docker-dev: ## Start development environment
	docker-compose up redforge-dev

docker-compose-up: ## Start full development stack
	docker-compose --profile full up -d

docker-compose-down: ## Stop development stack
	docker-compose down

# Development targets
dev: ## Start development environment
	poetry shell

format: ## Format code
	poetry run black redforge/ tests/
	poetry run isort redforge/ tests/

check: lint test ## Run all checks (lint + test)

# E2E Testing
test-core: ## Run core E2E tests (Product Hunt ready)
	./manual_test_script_core.sh

test-paid-flow: ## Run paid flow tests (requires Stripe setup)
	@echo "🔧 Checking Stripe environment..."
	@if [ -z "$(STRIPE_API_KEY)" ] || [ -z "$(PRICE_STARTER)" ]; then \
		echo "❌ Set STRIPE_API_KEY and PRICE_STARTER first"; \
		echo "💡 Run: ./setup_stripe_env.sh"; \
		exit 1; \
	fi
	@echo "✅ Environment ready, running paid flow tests..."
	./paid_flow_test.sh

test-e2e: test-core ## Alias for core E2E tests

# CLI testing shortcuts
cli-help: ## Test CLI help command
	poetry run python -m redforge.cli --help

cli-version: ## Test CLI version command  
	poetry run python -m redforge.cli version

cli-doctor: ## Test CLI doctor command
	poetry run python -m redforge.cli doctor

cli-list: ## Test CLI list-attacks command
	poetry run python -m redforge.cli list-attacks

cli-dry-run: ## Test CLI dry run
	poetry run python -m redforge.cli scan gpt-4 --dry-run --max-requests 5

# Release targets
bump-version: ## Bump version (use VERSION=x.y.z)
	poetry version $(VERSION)
	git add pyproject.toml
	git commit -m "chore: bump version to $(VERSION)"
	git tag v$(VERSION)

release: build ## Build and prepare release
	@echo "Built package for release. Next steps:"
	@echo "1. git push origin main"
	@echo "2. git push origin --tags"
	@echo "3. poetry publish"

# Documentation
docs-build: ## Build documentation
	poetry run mkdocs build

docs-serve: ## Serve documentation locally
	poetry run mkdocs serve

# Issue PS-2 specific targets
schema-export: ## Export JSON schema for reports
	poetry run python -c "from redforge.models.scan_result import ScanResult; import json; print(json.dumps(ScanResult.schema(), indent=2))" > docs/schema/scan-result.json

schema-validate: ## Validate example reports against schema
	poetry run python scripts/validate_schema.py

# GitHub workflow testing
gh-test: ## Test GitHub Actions locally (requires act)
	act -j split-for-ai --env-file .env.local

# Sprint S-1 deliverables checklist
s1-checklist: ## Verify Sprint S-1 deliverables
	@echo "🎯 Sprint S-1 Deliverable Checklist:"
	@echo ""
	@echo "✅ Dockerised CLI:"
	@docker --version > /dev/null && echo "  ✓ Docker available" || echo "  ❌ Docker not found"
	@test -f Dockerfile && echo "  ✓ Dockerfile exists" || echo "  ❌ Dockerfile missing"
	@test -f docker-compose.yml && echo "  ✓ docker-compose.yml exists" || echo "  ❌ docker-compose.yml missing"
	@echo ""
	@echo "✅ Poetry Environment:"
	@poetry --version > /dev/null && echo "  ✓ Poetry available" || echo "  ❌ Poetry not found"  
	@test -f pyproject.toml && echo "  ✓ pyproject.toml exists" || echo "  ❌ pyproject.toml missing"
	@echo ""
	@echo "✅ CLI Entrypoint:"
	@test -f redforge/cli.py && echo "  ✓ CLI module exists" || echo "  ❌ CLI module missing"
	@test -f redforge/__init__.py && echo "  ✓ Package init exists" || echo "  ❌ Package init missing"
	@echo ""
	@echo "✅ Report Schema (Issue PS-2):"
	@test -f redforge/models/scan_result.py && echo "  ✓ Scan result models exist" || echo "  ❌ Models missing"
	@test -f docs/cli-spec.md && echo "  ✓ CLI specification exists" || echo "  ❌ CLI spec missing"
	@echo ""
	@echo "📋 Next: Draft PR #12 → Design Partner Testing → 500 downloads target"

# Example usage
example-scan: ## Run example scan (requires OPENAI_API_KEY)
	@echo "Running example scan with RedForge CLI..."
	poetry run python -m redforge.cli scan gpt-3.5-turbo \
		--output ./reports/example \
		--format json \
		--max-requests 10 \
		--dry-run