# =============================================================================
# HeyCloud - Cloud-Native Real-Time Streaming Analytics Platform
# =============================================================================

.PHONY: help init plan apply destroy producer-build producer-run frontend-dev \
        test lint clean package-lambdas

# Default target
help: ## Show this help
	@echo "HeyCloud - Available Commands:"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Terraform
# =============================================================================

init: ## Initialize Terraform
	cd infrastructure/terraform && terraform init

plan: ## Run Terraform plan (dev)
	cd infrastructure/terraform && terraform plan -var-file=../environments/dev.tfvars

apply: ## Apply Terraform changes (dev)
	cd infrastructure/terraform && terraform apply -var-file=../environments/dev.tfvars

destroy: ## Destroy all infrastructure (dev)
	cd infrastructure/terraform && terraform destroy -var-file=../environments/dev.tfvars

fmt: ## Format Terraform files
	cd infrastructure/terraform && terraform fmt -recursive

validate: ## Validate Terraform configuration
	cd infrastructure/terraform && terraform validate

# =============================================================================
# Docker / Event Producer
# =============================================================================

producer-build: ## Build the event producer Docker image
	docker build -t heycloud-producer ./services/event-producer

producer-run: ## Run the event producer container
	docker run --rm --env-file .env heycloud-producer

docker-up: ## Start all services with docker-compose
	docker-compose up --build

docker-down: ## Stop all docker-compose services
	docker-compose down

# =============================================================================
# Frontend
# =============================================================================

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	python -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -v --tb=short

test-integration: ## Run integration tests
	python -m pytest tests/integration/ -v --tb=short

test-coverage: ## Run tests with coverage
	python -m pytest tests/ -v --cov=services --cov=api --cov-report=html

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linters
	ruff check services/ api/ tests/
	cd infrastructure/terraform && terraform fmt -check -recursive

format: ## Auto-format code
	ruff format services/ api/ tests/
	cd infrastructure/terraform && terraform fmt -recursive

security-scan: ## Run security scans
	bandit -r services/ api/ -ll
	cd infrastructure/terraform && tfsec .

# =============================================================================
# Lambda Packaging
# =============================================================================

package-lambdas: ## Package Lambda functions for deployment
	@echo "Packaging stream-processor..."
	cd services/stream-processor && \
		pip install -r requirements.txt -t package/ && \
		cp -r *.py processors/ storage/ models/ utils/ package/ && \
		cd package && zip -r ../../stream-processor.zip .
	@echo "Packaging analytics-api..."
	cd api/analytics && \
		pip install -r requirements.txt -t package/ && \
		cp -r *.py queries/ utils/ package/ && \
		cd package && zip -r ../../analytics-api.zip .

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	rm -f *.zip
	rm -rf services/stream-processor/package/
	rm -rf api/analytics/package/

seed-data: ## Seed sample data for testing
	python scripts/seed-data.py

test-pipeline: ## Test the complete pipeline end-to-end
	python scripts/test-pipeline.py
