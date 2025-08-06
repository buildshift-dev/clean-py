# Makefile for Clean Architecture Python

.PHONY: help install lint format type-check test test-unit test-integration docs clean run-api run-streamlit troubleshoot test-api

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 If any command fails, it will show specific fix instructions."
	@echo "💡 For comprehensive troubleshooting, run: make troubleshoot"

install: ## Install production dependencies only
	pip install -r requirements.txt

install-dev: ## Install development dependencies (includes production)
	pip install -r requirements-dev.txt

setup-dev: ## Setup development environment (upgrade pip + install dev deps + editable package)
	@echo "🔧 Setting up development environment..."
	@echo "Upgrading pip to latest version..."
	@python -m pip install --upgrade pip
	@echo "Installing development dependencies..."
	@pip install -r requirements-dev.txt
	@echo "Installing package in editable mode..."
	@pip install -e .
	@echo "✅ Development environment setup complete!"

lint: ## Run all linting tools
	@echo "Running ruff..."
	@if ! ruff check src tests; then \
		echo ""; \
		echo "❌ Ruff linting failed. To fix:"; \
		echo "  • Auto-fix issues: ruff check --fix src tests"; \
		echo "  • Auto-fix with unsafe changes: ruff check --fix --unsafe-fixes src tests"; \
		echo "  • See specific rules: https://docs.astral.sh/ruff/rules/"; \
		exit 1; \
	fi
	@echo "Running pylint..."
	@if ! pylint src --fail-under=9.0; then \
		echo ""; \
		echo "❌ Pylint failed. To fix:"; \
		echo "  • Check specific issues above"; \
		echo "  • Disable specific rules in pyproject.toml [tool.pylint.messages_control]"; \
		echo "  • Current threshold: 9.0/10 (see --fail-under in Makefile)"; \
		exit 1; \
	fi
	@echo "✅ All linting passed!"
	@echo "Type checking available with: make type-check"

format: ## Format code with ruff
	@echo "Formatting code with ruff..."
	@if ! ruff format src tests; then \
		echo ""; \
		echo "❌ Ruff formatting failed. To fix:"; \
		echo "  • Check file permissions"; \
		echo "  • Ensure files are valid Python syntax"; \
		echo "  • Check ruff configuration in pyproject.toml"; \
		exit 1; \
	fi
	@echo "✅ Code formatting completed!"

type-check: ## Run type checking with pyright
	@echo "Running type checking with pyright..."
	@if ! pyright src tests; then \
		echo ""; \
		echo "❌ Type checking failed. To fix:"; \
		echo "  • Add missing type annotations"; \
		echo "  • Use Union[Type, None] for optional types"; \
		echo "  • Check import statements and module paths"; \
		echo "  • See coding standards: docs/coding-standards.md"; \
		echo "  • Pyright config: https://microsoft.github.io/pyright/"; \
		exit 1; \
	fi
	@echo "✅ Type checking passed!"

test: ## Run all tests
	@echo "Running all tests..."
	@if ! pytest; then \
		echo ""; \
		echo "❌ Tests failed. To fix:"; \
		echo "  • Check test output above for specific failures"; \
		echo "  • Run individual test: pytest tests/path/to/test_file.py::test_name -v"; \
		echo "  • Debug with: pytest --pdb"; \
		echo "  • Check imports work: make setup-dev"; \
		exit 1; \
	fi
	@echo "✅ All tests passed!"

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@if ! pytest tests/unit/ -v; then \
		echo ""; \
		echo "❌ Unit tests failed. To fix:"; \
		echo "  • Check specific test failures above"; \
		echo "  • Ensure development setup: make setup-dev"; \
		echo "  • Run single test: pytest tests/unit/path/test_file.py::TestClass::test_method -v"; \
		exit 1; \
	fi
	@echo "✅ Unit tests passed!"

test-integration: ## Run integration tests only (when they exist)
	@if [ -n "$$(find tests/integration -name '*.py' -type f 2>/dev/null)" ]; then \
		pytest tests/integration/ -v; \
	else \
		echo "No integration tests found in tests/integration/"; \
	fi

test-coverage: ## Run tests with coverage (requires pytest-cov)
	@echo "Coverage requires: pip install pytest-cov"
	@echo "Then run: pytest --cov=src --cov-report=html --cov-report=term"

docs: ## Generate documentation with MkDocs
	@echo "📚 Documentation generation not yet set up"
	@echo ""
	@echo "To set up documentation:"
	@echo "  1. pip install mkdocs mkdocs-material"
	@echo "  2. mkdocs new . --force"
	@echo "  3. Configure mkdocs.yml for project structure"
	@echo "  4. Uncomment 'mkdocs build' line in Makefile"
	@echo ""
	# mkdocs build

clean: ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf site/

run-api: ## Run FastAPI development server
	@echo "Starting FastAPI development server..."
	@echo "API will be available at: http://localhost:8000"
	@echo "API docs will be available at: http://localhost:8000/docs"
	@echo "Press CTRL+C to stop the server"
	@echo ""
	uvicorn src.presentation.main:app --reload --host 127.0.0.1 --port 8000

run-streamlit: ## Run Streamlit demo app
	@echo "Starting Streamlit demo application..."
	@echo "App will be available at: http://localhost:8501"
	@echo "Features:"
	@echo "  • Toggle between Mock Data and FastAPI Server"
	@echo "  • Create customers using Clean Architecture"
	@echo "  • View data from both sources"
	@echo "Press CTRL+C to stop the server"
	@echo ""
	streamlit run src/streamlit_app.py

test-api: ## Test FastAPI application imports and routes
	@echo "Testing FastAPI application..."
	@python -c "from src.presentation.main import app; print('✅ FastAPI app imports successfully'); print('Available endpoints:'); [print(f'  {(\", \".join(route.methods) if hasattr(route, \"methods\") and route.methods else \"N/A\"):<10} {route.path}') for route in app.routes if hasattr(route, 'path')]"

# Quality checks - enforce type hints and code quality
check-types: ## Strict type checking
	@echo "Checking for missing type annotations..."
	ruff check src tests --select ANN
	@echo "Running strict pyright checks..."
	pyright --warnings src tests

security: ## Run security analysis
	@echo "Running security analysis with Bandit..."
	@if ! bandit -r src/ -ll; then \
		echo ""; \
		echo "❌ Security scan found issues. To fix:"; \
		echo "  • Review security issues above"; \
		echo "  • Skip specific tests: bandit -r src/ --skip B101"; \
		echo "  • Generate report: bandit -r src/ -f html -o security-report.html"; \
		exit 1; \
	fi
	@echo "✅ Security scan passed!"

dependency-audit: ## Check dependencies for known vulnerabilities
	@echo "Checking dependencies for vulnerabilities..."
	@if command -v safety >/dev/null 2>&1; then \
		safety check; \
	elif command -v pip-audit >/dev/null 2>&1; then \
		pip-audit; \
	else \
		echo "⚠️  No dependency scanner found. Install with:"; \
		echo "  pip install safety  # or"; \
		echo "  pip install pip-audit"; \
	fi

# Pre-commit style checks
pre-commit: format lint type-check security test-unit ## Run all pre-commit checks

# CI pipeline simulation
ci: ## Simulate CI pipeline
	@echo "=== Installing dependencies ==="
	make install-dev
	@echo "=== Formatting check ==="
	ruff format --check src tests
	@echo "=== Linting ==="
	make lint
	@echo "=== Type checking ==="
	make type-check
	@echo "=== Security scanning ==="
	make security
	@echo "=== Running tests ==="
	make test
	@echo "=== All checks passed! ==="

troubleshoot: ## Comprehensive troubleshooting guide
	@echo "🔧 Clean Architecture Python - Troubleshooting Guide"
	@echo "================================================"
	@echo ""
	@echo "📋 Environment Check:"
	@python --version || echo "❌ Python not found - install Python 3.11+"
	@pip --version || echo "❌ pip not found"
	@echo ""
	@echo "📋 Virtual Environment:"
	@if [ -d ".venv" ]; then \
		echo "✅ .venv directory exists"; \
		if [ "$$VIRTUAL_ENV" ]; then \
			echo "✅ Virtual environment activated: $$VIRTUAL_ENV"; \
		else \
			echo "⚠️  Virtual environment not activated. Run: source .venv/bin/activate"; \
		fi; \
	else \
		echo "❌ .venv not found. Create with: python -m venv .venv"; \
	fi
	@echo ""
	@echo "📋 Dependencies:"
	@if [ -f "requirements.txt" ]; then \
		echo "✅ requirements.txt found"; \
	else \
		echo "❌ requirements.txt missing"; \
	fi
	@pip show ruff > /dev/null 2>&1 && echo "✅ ruff installed" || echo "❌ ruff missing - run: make setup-dev"
	@pip show pytest > /dev/null 2>&1 && echo "✅ pytest installed" || echo "❌ pytest missing - run: make setup-dev"
	@echo ""
	@echo "📋 Package Installation:"
	@if pip show clean-py > /dev/null 2>&1; then \
		echo "✅ clean-py installed in editable mode"; \
	else \
		echo "❌ clean-py not installed - run: make setup-dev"; \
	fi
	@echo ""
	@echo "📋 Common Fixes:"
	@echo "  • Import errors: make setup-dev"
	@echo "  • Linting failures: ruff check --fix src tests"
	@echo "  • Test failures: Check virtual environment activation"
	@echo "  • Type errors: See docs/coding-standards.md"
	@echo ""
	@echo "📋 Quick Setup (if starting fresh):"
	@echo "  1. source .venv/bin/activate"
	@echo "  2. make setup-dev"
	@echo "  3. make test"
	@echo ""
	@echo "📋 API Testing:"
	@if python -c "from src.presentation.main import app" 2>/dev/null; then \
		echo "✅ FastAPI app imports successfully"; \
	else \
		echo "❌ FastAPI app import failed - check dependencies"; \
	fi
	@echo ""
	@echo "📋 Documentation:"
	@echo "  • Coding standards: docs/coding-standards.md"
	@echo "  • VS Code setup: docs/vscode-test-discovery.md"
	@echo ""
	@echo "📋 Available Services:"
	@echo "  • API server: make run-api (http://localhost:8000)"
	@echo "  • API docs: http://localhost:8000/docs (when server running)"
	@echo "  • Streamlit demo: make run-streamlit"
	@echo "  • Test API: make test-api"
	@echo ""
	@echo "📋 Security Commands:"
	@echo "  • Security scan: make security"
	@echo "  • Dependency audit: make dependency-audit"