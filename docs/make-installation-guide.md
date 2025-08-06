# Make Installation and Usage Guide

## Overview
Make is a build automation tool that runs tasks defined in a `Makefile`. Our project uses Make to simplify common development tasks like linting, testing, and running applications.

## Installing Make

### macOS

**Option 1: Using Homebrew (Recommended)**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install make
brew install make
```

**Option 2: Using Xcode Command Line Tools**
```bash
# This installs make along with other development tools
xcode-select --install
```

**Verify Installation**
```bash
make --version
# Should output: GNU Make 4.3 (or similar)
```

### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install make
sudo apt install make

# Verify installation
make --version
```

### Linux (CentOS/RHEL/Fedora)
```bash
# For CentOS/RHEL
sudo yum install make

# For Fedora
sudo dnf install make

# Verify installation
make --version
```

### Windows

**Option 1: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey if you don't have it
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install make
choco install make
```

**Option 2: Using Windows Subsystem for Linux (WSL)**
```bash
# Install WSL2 first, then in WSL terminal:
sudo apt update
sudo apt install make
```

**Option 3: Using MSYS2**
1. Download and install MSYS2 from https://www.msys2.org/
2. Open MSYS2 terminal
3. Run: `pacman -S make`

**Option 4: Using Git Bash**
- Git for Windows includes make
- Download from https://git-scm.com/download/win
- Use Git Bash terminal for make commands

**Verify Installation (Windows)**
```bash
# In PowerShell, Command Prompt, or Git Bash
make --version
```

## Using Make in This Project

### Basic Make Concepts

**Makefile Structure**
```makefile
target: dependencies
	command1
	command2
```

**Key Points:**
- Commands must be indented with **tabs**, not spaces
- Each target can have dependencies
- Make only runs targets if dependencies have changed

### Available Commands

Display all available commands:
```bash
make help
```

### Development Workflow Commands

**Initial Setup**
```bash
# Install all project dependencies
make install
```

**Code Quality**
```bash
# Format code automatically
make format

# Run all linting tools (ruff, pylint, pyright)
make lint

# Run strict type checking only
make type-check

# Check for missing type annotations
make check-types
```

**Testing**
```bash
# Run all tests
make test

# Run only fast unit tests
make test-unit

# Run integration tests (requires database)
make test-integration

# Run tests with coverage report
make test-coverage
```

**Running Applications**
```bash
# Run Streamlit demo
make run-streamlit

# Run FastAPI development server
make run-api
```

**Documentation**
```bash
# Generate project documentation (placeholder)
make docs
```

**Maintenance**
```bash
# Clean cache and temporary files
make clean
```

**Workflow Commands**
```bash
# Run all pre-commit checks (format + lint + type-check + test-unit)
make pre-commit

# Simulate complete CI pipeline
make ci
```

### Command Examples with Output

**Running Tests**
```bash
$ make test-unit
pytest tests/unit/ -v
============================= test session starts ==============================
platform darwin -- Python 3.9.16
collected 8 items

tests/unit/domain/test_customer.py::TestCustomer::test_customer_creation PASSED
tests/unit/domain/test_customer.py::TestCustomer::test_customer_deactivate PASSED
tests/unit/domain/test_order.py::TestOrder::test_order_creation PASSED
...
============================== 8 passed in 0.12s ==============================
```

**Code Formatting**
```bash
$ make format
ruff format src tests
All files formatted successfully!
```

**Linting**
```bash
$ make lint
Running ruff...
All checks passed!
Running pylint...
Your code has been rated at 10.00/10
Running pyright...
0 errors, 0 warnings, 0 informations
```

### Command Chaining

Make allows running multiple commands in sequence:
```bash
# Run format, then lint, then test
make format lint test

# Or use our workflow commands
make pre-commit  # Equivalent to: format lint type-check test-unit
```

### Parallel Execution

Run multiple targets in parallel:
```bash
# Run tests and linting simultaneously (if independent)
make -j2 test lint
```

## Troubleshooting Make

### Common Issues

**"make: command not found"**
- Make is not installed or not in PATH
- Follow installation instructions above
- On Windows, ensure you're using the correct terminal (Git Bash, WSL, etc.)

**"No targets specified and no makefile found"**
- You're not in the project root directory
- Navigate to the directory containing `Makefile`
```bash
cd /path/to/clean-py
make help
```

**"make: *** No rule to make target"**
- Check available targets with `make help`
- Verify you typed the command correctly
- Example: `make test-untit` should be `make test-unit`

**Permission Issues (Linux/macOS)**
```bash
# If you get permission errors
sudo make install

# Better approach: fix Python environment permissions
python -m venv venv
source venv/bin/activate
make install
```

**Tab vs Spaces Error**
```
Makefile:10: *** missing separator. Stop.
```
- Makefile commands must use tabs, not spaces
- Configure your editor to show tabs vs spaces
- Most IDEs can automatically convert spaces to tabs in Makefiles

### Windows-Specific Issues

**Using PowerShell**
```powershell
# If make commands don't work in PowerShell
# Use Git Bash or WSL instead
```

**Path Issues**
```bash
# Add make to PATH if needed
# In Git Bash or WSL, this usually isn't necessary
```

### Make Alternatives on Windows

If you can't install Make, you can run commands directly:

```bash
# Instead of: make install
pip install -r requirements.txt

# Instead of: make format
ruff format src tests

# Instead of: make lint
ruff check src tests
pylint src
pyright src tests

# Instead of: make test
pytest

# Instead of: make run-streamlit
streamlit run src/streamlit_app.py
```

## Best Practices

### Development Workflow
```bash
# Daily development routine
make clean          # Start fresh
make install        # Ensure dependencies are up to date
make format         # Format any new code
make lint           # Check code quality
make test-unit      # Run fast tests during development
```

### Before Committing
```bash
# Complete quality check
make pre-commit

# Or run full CI pipeline locally
make ci
```

### Performance Tips
```bash
# Run only what you need during development
make test-unit      # Fast tests only

# Use parallel execution when possible
make -j4 format lint test-unit
```

### Customizing Make

You can add your own targets to the Makefile:
```makefile
# Add custom targets for your workflow
.PHONY: quick-check
quick-check: format test-unit  ## Quick development check
	@echo "Quick check completed!"
```

## IDE Integration

### VS Code
- Install "Makefile Tools" extension
- Tasks will appear in Command Palette
- Can run make targets from GUI

### PyCharm
- External Tools → Add Make
- Configure with working directory and arguments

### Terminal Integration
Most developers prefer running make commands directly in terminal for immediate feedback and control.

---

*For project-specific make commands, run `make help` in the project root directory.*