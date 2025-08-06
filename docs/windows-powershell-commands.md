# Windows PowerShell Commands (Make Alternative)

## Overview
This guide provides PowerShell equivalents for all Makefile commands, allowing Windows users to run development tasks without installing Make.

## Prerequisites
- PowerShell 5.1+ (comes with Windows 10/11)
- Python 3.9+ installed and in PATH
- Git installed

## PowerShell Command Reference

### Setup Commands

**Help - Show Available Commands**
```powershell
# Display this help information
Get-Content docs\windows-powershell-commands.md | Select-String "^##.*Commands" -A 50
```

**Install Dependencies**
```powershell
# Equivalent to: make install (production only)
pip install -r requirements.txt

# Equivalent to: make install-dev (development dependencies - includes production)
pip install -r requirements-dev.txt
```

**Setup Development Environment**
```powershell
# Equivalent to: make setup-dev
pip install -r requirements-dev.txt
pip install -e .
```

**Clean Cache and Temporary Files**
```powershell
# Equivalent to: make clean
Get-ChildItem -Path . -Recurse -Name "*.pyc" | Remove-Item -Force
Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Directory -Name ".pytest_cache" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Directory -Name ".mypy_cache" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -Directory -Name ".ruff_cache" | Remove-Item -Recurse -Force
if (Test-Path "htmlcov") { Remove-Item -Path "htmlcov" -Recurse -Force }
```

### Code Quality Commands

**Format Code**
```powershell
# Equivalent to: make format
ruff format src tests
```

**Run All Linting**
```powershell
# Equivalent to: make lint
Write-Host "Running ruff..." -ForegroundColor Yellow
ruff check src tests
Write-Host "Running pylint..." -ForegroundColor Yellow
pylint src
Write-Host "Running pyright..." -ForegroundColor Yellow
pyright src tests
```

**Type Checking Only**
```powershell
# Equivalent to: make type-check
pyright src tests
```

**Check for Missing Type Annotations**
```powershell
# Equivalent to: make check-types
Write-Host "Checking for missing type annotations..." -ForegroundColor Yellow
ruff check src tests --select ANN
Write-Host "Running strict pyright checks..." -ForegroundColor Yellow
pyright --warnings src tests
```

**Security Analysis**
```powershell
# Equivalent to: make security
Write-Host "Running security analysis with Bandit..." -ForegroundColor Yellow
bandit -r src/ -ll
```

**Dependency Vulnerability Check**
```powershell
# Equivalent to: make dependency-audit
Write-Host "Checking dependencies for vulnerabilities..." -ForegroundColor Yellow
if (Get-Command safety -ErrorAction SilentlyContinue) {
    safety check
} elseif (Get-Command pip-audit -ErrorAction SilentlyContinue) {
    pip-audit
} else {
    Write-Host "⚠️  No dependency scanner found. Install with:" -ForegroundColor Yellow
    Write-Host "  pip install safety  # or"
    Write-Host "  pip install pip-audit"
}
```

### Testing Commands

**Run All Tests**
```powershell
# Equivalent to: make test
pytest
```

**Run Unit Tests Only**
```powershell
# Equivalent to: make test-unit
pytest tests\unit\ -v
```

**Run Integration Tests Only**
```powershell
# Equivalent to: make test-integration
pytest tests\integration\ -v
```

**Run Tests with Coverage**
```powershell
# Equivalent to: make test-coverage
pytest --cov=src --cov-report=html --cov-report=term
# Open coverage report
if (Test-Path "htmlcov\index.html") {
    Start-Process "htmlcov\index.html"
}
```

### Application Commands

**Run Streamlit Demo**
```powershell
# Equivalent to: make run-streamlit
streamlit run src/streamlit_app.py
```

**Run FastAPI Development Server**
```powershell
# Equivalent to: make run-api
uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000
```

### Workflow Commands

**Pre-commit Checks**
```powershell
# Equivalent to: make pre-commit
Write-Host "=== Running Pre-commit Checks ===" -ForegroundColor Green

Write-Host "1. Formatting code..." -ForegroundColor Yellow
ruff format src tests

Write-Host "2. Running linting..." -ForegroundColor Yellow
ruff check src tests
pylint src
pyright src tests

Write-Host "3. Running security scan..." -ForegroundColor Yellow
bandit -r src/ -ll

Write-Host "4. Running unit tests..." -ForegroundColor Yellow
pytest tests\unit\ -v

Write-Host "=== Pre-commit checks completed ===" -ForegroundColor Green
```

**Simulate CI Pipeline**
```powershell
# Equivalent to: make ci
Write-Host "=== Simulating CI Pipeline ===" -ForegroundColor Green

Write-Host "=== Installing dependencies ===" -ForegroundColor Yellow
pip install -r requirements-dev.txt

Write-Host "=== Checking code formatting ===" -ForegroundColor Yellow
ruff format --check src tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Code formatting check failed"
    exit 1
}

Write-Host "=== Running linting ===" -ForegroundColor Yellow
ruff check src tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Linting failed"
    exit 1
}

pylint src
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pylint failed"
    exit 1
}

pyright src tests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Type checking failed"
    exit 1
}

Write-Host "=== Security scanning ===" -ForegroundColor Yellow
bandit -r src/ -ll
if ($LASTEXITCODE -ne 0) {
    Write-Error "Security scan failed"
    exit 1
}

Write-Host "=== Running all tests ===" -ForegroundColor Yellow
pytest
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed"
    exit 1
}

Write-Host "=== All CI checks passed! ===" -ForegroundColor Green
```

## PowerShell Scripts

### Create Reusable Scripts

You can create `.ps1` script files for commonly used commands:

**setup.ps1**
```powershell
# Initial project setup
Write-Host "Setting up Clean Architecture Python..." -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Setup completed! Run 'venv\Scripts\Activate.ps1' to activate the environment." -ForegroundColor Green
```

**quality-check.ps1**
```powershell
# Run all quality checks
param(
    [switch]$Fix = $false
)

Write-Host "Running code quality checks..." -ForegroundColor Green

if ($Fix) {
    Write-Host "Auto-fixing issues..." -ForegroundColor Yellow
    ruff format src tests
    ruff check src tests --fix
} else {
    Write-Host "Checking format..." -ForegroundColor Yellow
    ruff format --check src tests
    
    Write-Host "Running linting..." -ForegroundColor Yellow
    ruff check src tests
}

Write-Host "Running pylint..." -ForegroundColor Yellow
pylint src

Write-Host "Running type checking..." -ForegroundColor Yellow
pyright src tests

Write-Host "Quality checks completed!" -ForegroundColor Green
```

**test-runner.ps1**
```powershell
# Test runner with options
param(
    [string]$Type = "all",
    [switch]$Coverage = $false,
    [string]$Pattern = ""
)

Write-Host "Running tests..." -ForegroundColor Green

$testArgs = @()

switch ($Type) {
    "unit" { 
        $testArgs += "tests\unit\"
        Write-Host "Running unit tests only..." -ForegroundColor Yellow
    }
    "integration" { 
        $testArgs += "tests\integration\"
        Write-Host "Running integration tests only..." -ForegroundColor Yellow
    }
    default { 
        Write-Host "Running all tests..." -ForegroundColor Yellow
    }
}

if ($Coverage) {
    $testArgs += "--cov=src", "--cov-report=html", "--cov-report=term"
}

if ($Pattern) {
    $testArgs += "-k", $Pattern
}

$testArgs += "-v"

pytest @testArgs

if ($Coverage -and (Test-Path "htmlcov\index.html")) {
    Write-Host "Opening coverage report..." -ForegroundColor Yellow
    Start-Process "htmlcov\index.html"
}
```

### Using the Scripts

**Make scripts executable and run them:**
```powershell
# Allow script execution (run once)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
.\setup.ps1

# Run quality checks
.\quality-check.ps1

# Run quality checks with auto-fix
.\quality-check.ps1 -Fix

# Run different types of tests
.\test-runner.ps1 -Type unit
.\test-runner.ps1 -Type integration  
.\test-runner.ps1 -Coverage
.\test-runner.ps1 -Pattern "test_customer"
```

## Command Aliases

### Create PowerShell Aliases

Add these to your PowerShell profile (`$PROFILE`):

```powershell
# Development aliases
function dev-install { pip install -r requirements.txt }
function dev-format { ruff format src tests }
function dev-lint { 
    ruff check src tests
    pylint src 
    pyright src tests
}
function dev-test { pytest }
function dev-test-unit { pytest tests\unit\ -v }
function dev-run-app { streamlit run src/streamlit_app.py }
function dev-run-api { uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000 }
function dev-security { bandit -r src/ -ll }
function dev-audit { if (Get-Command safety -ErrorAction SilentlyContinue) { safety check } else { pip-audit } }
function dev-clean {
    Get-ChildItem -Path . -Recurse -Name "*.pyc" | Remove-Item -Force
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path . -Recurse -Directory -Name ".pytest_cache" | Remove-Item -Recurse -Force
}

# Set aliases
Set-Alias -Name install -Value dev-install
Set-Alias -Name format -Value dev-format
Set-Alias -Name lint -Value dev-lint
Set-Alias -Name test -Value dev-test
Set-Alias -Name test-unit -Value dev-test-unit
Set-Alias -Name run-app -Value dev-run-app
Set-Alias -Name run-api -Value dev-run-api
Set-Alias -Name security -Value dev-security
Set-Alias -Name audit -Value dev-audit
Set-Alias -Name clean -Value dev-clean
```

**Usage after setting up aliases:**
```powershell
install       # Same as: pip install -r requirements.txt
format        # Same as: ruff format src tests
lint          # Same as: ruff + pylint + pyright
test          # Same as: pytest
test-unit     # Same as: pytest tests\unit\ -v
run-app       # Same as: streamlit run src/streamlit_app.py
security      # Same as: bandit -r src/ -ll
audit         # Same as: safety check or pip-audit
clean         # Clean cache files
```

## Environment Variables

### Set up PowerShell Environment

**Add to PowerShell profile (`$PROFILE`):**
```powershell
# Clean Architecture Python environment
$env:PYTHONPATH = "$PWD\src;$env:PYTHONPATH"
$env:PYTEST_CURRENT_TEST = ""

# Useful functions
function Show-DemoCommands {
    Write-Host "Clean Architecture Python Commands:" -ForegroundColor Green
    Write-Host "  install      - Install dependencies" -ForegroundColor Yellow
    Write-Host "  format       - Format code" -ForegroundColor Yellow
    Write-Host "  lint         - Run linting" -ForegroundColor Yellow
    Write-Host "  test         - Run all tests" -ForegroundColor Yellow
    Write-Host "  test-unit    - Run unit tests" -ForegroundColor Yellow
    Write-Host "  run-app      - Run Streamlit app" -ForegroundColor Yellow
    Write-Host "  run-api      - Run FastAPI server" -ForegroundColor Yellow
    Write-Host "  security     - Run security scan" -ForegroundColor Yellow
    Write-Host "  audit        - Check dependencies" -ForegroundColor Yellow
    Write-Host "  clean        - Clean cache files" -ForegroundColor Yellow
}

# Show commands when profile loads
Show-DemoCommands
```

## VS Code Integration

### Tasks Configuration

Create `.vscode\tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Install Dependencies",
            "type": "shell",
            "command": "pip",
            "args": ["install", "-r", "requirements.txt"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "ruff",
            "args": ["format", "src", "tests"],
            "group": "build"
        },
        {
            "label": "Run Linting",
            "type": "shell",
            "command": "powershell",
            "args": [
                "-Command",
                "ruff check src tests; pylint src; pyright src tests"
            ],
            "group": "test"
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "pytest",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true
            }
        },
        {
            "label": "Run Streamlit",
            "type": "shell",
            "command": "streamlit",
            "args": ["run", "src/streamlit_app.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": true
            }
        }
    ]
}
```

### Keyboard Shortcuts

Add to `.vscode\keybindings.json`:
```json
[
    {
        "key": "ctrl+shift+t",
        "command": "workbench.action.tasks.runTask",
        "args": "Run Tests"
    },
    {
        "key": "ctrl+shift+f",
        "command": "workbench.action.tasks.runTask", 
        "args": "Format Code"
    },
    {
        "key": "ctrl+shift+l",
        "command": "workbench.action.tasks.runTask",
        "args": "Run Linting"
    }
]
```

## Quick Reference

### Essential Commands
```powershell
# Setup
pip install -r requirements.txt
venv\Scripts\Activate.ps1

# Development
ruff format src tests                    # Format code
ruff check src tests                     # Quick lint
pytest tests\unit\ -v                   # Fast tests
streamlit run src/streamlit_app.py           # Run demo

# Quality checks
ruff check src tests; pylint src; pyright src tests  # Full lint
pytest --cov=src --cov-report=html      # Test with coverage

# Applications
streamlit run src/streamlit_app.py           # Interactive demo
uvicorn src.presentation.main:app --reload  # API server
```

### One-liner Quality Check
```powershell
ruff format src tests; ruff check src tests; pylint src; pyright src tests; pytest tests\unit\ -v
```

---

*These commands provide the same functionality as the Makefile for Windows users who prefer PowerShell or cannot install Make.*