# Python Security Guide for Production Applications

## Overview

This guide outlines security best practices and tools for Python applications, with a focus on static analysis, dependency management, and secure coding practices. The recommendations are based on OWASP guidelines and industry standards.

## Table of Contents

1. [Static Security Analysis](#static-security-analysis)
2. [Dependency Security](#dependency-security)
3. [Secure Coding Practices](#secure-coding-practices)
4. [Infrastructure Security](#infrastructure-security)
5. [CI/CD Security Pipeline](#cicd-security-pipeline)
6. [Monitoring and Response](#monitoring-and-response)

## Static Security Analysis

### Primary Tool: Bandit

**Bandit** is the industry standard for Python static security analysis. It scans Python code for common security vulnerabilities and provides actionable feedback.

#### Installation and Basic Usage

```bash
# Install Bandit
pip install bandit

# Basic scan
bandit -r src/

# High confidence issues only
bandit -r src/ -ll

# Skip test files (common practice)
bandit -r src/ --skip B101

# Generate reports
bandit -r src/ -f json -o security-report.json
bandit -r src/ -f html -o security-report.html
```

#### Common Issues Detected

```python
# 1. Hardcoded Passwords/Secrets ❌
API_KEY = "sk-1234567890abcdef"  # Bandit: B105
DATABASE_PASSWORD = "admin123"   # Bandit: B105

# Better: Use environment variables ✅
import os
API_KEY = os.getenv("API_KEY")
DATABASE_PASSWORD = os.getenv("DB_PASSWORD")

# 2. SQL Injection Vulnerabilities ❌
query = f"SELECT * FROM users WHERE id = {user_id}"  # Bandit: B608

# Better: Use parameterized queries ✅
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# 3. Insecure Random Numbers ❌
import random
session_token = str(random.randint(1000, 9999))  # Bandit: B311

# Better: Use cryptographically secure random ✅
import secrets
session_token = secrets.token_urlsafe(32)

# 4. Command Injection ❌
import subprocess
subprocess.call(f"ping {user_input}", shell=True)  # Bandit: B602

# Better: Use argument lists ✅
subprocess.call(["ping", user_input])

# 5. Insecure Temporary Files ❌
import tempfile
temp_file = tempfile.mktemp()  # Bandit: B306

# Better: Use secure temporary files ✅
with tempfile.NamedTemporaryFile(delete=False) as temp_file:
    temp_file.write(data)
```

#### Configuration

Create `.bandit` configuration file:

```yaml
# .bandit
[bandit]
exclude: /tests
tests: B201,B301
skips: B101,B601
```

Or use `pyproject.toml`:

```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
tests = ["B201", "B301"]
skips = ["B101"]  # Skip assert_used in tests
```

### Complementary Tools

#### Safety - Dependency Vulnerability Scanner

```bash
# Install and run
pip install safety
safety check

# Check specific file
safety check -r requirements.txt

# Ignore specific vulnerabilities
safety check --ignore 12345
```

#### Semgrep - Advanced Pattern Analysis

```bash
# Install and run
pip install semgrep
semgrep --config=auto src/

# Python-specific rules
semgrep --config=python src/

# Custom rules
semgrep --config=./security-rules.yml src/
```

## Dependency Security

### Vulnerability Management

#### 1. Regular Dependency Audits

```bash
# Modern approach (PyPA official)
pip install pip-audit
pip-audit

# Traditional approach
pip install safety
safety check

# Check for outdated packages
pip list --outdated
```

#### 2. Dependency Pinning

```toml
# pyproject.toml - Pin major versions
dependencies = [
    "fastapi>=0.100.0,<1.0.0",
    "sqlalchemy>=2.0.0,<3.0.0",
    "pydantic>=2.0.0,<3.0.0",
]

# requirements.txt - Exact versions for production
fastapi==0.104.1
sqlalchemy==2.0.23
pydantic==2.5.0
```

#### 3. Automated Updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### Supply Chain Security

#### 1. Package Verification

```bash
# Verify package integrity
pip install --require-hashes -r requirements-hashed.txt

# Generate hashes
pip-compile --generate-hashes requirements.in
```

#### 2. Private Package Index

```bash
# Use trusted sources only
pip install --index-url https://your-private-pypi.com/simple/ package-name
```

## Secure Coding Practices

### 1. Input Validation

```python
# Use Pydantic for validation ✅
from pydantic import BaseModel, EmailStr, validator

class UserInput(BaseModel):
    email: EmailStr
    age: int
    
    @validator('age')
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError('Invalid age')
        return v

# Validate all external input
def process_user_data(raw_data: dict):
    try:
        user_data = UserInput(**raw_data)
        return user_data
    except BusinessRuleError as e:
        logger.error(f"Invalid input: {e}")
        raise ValueError("Invalid user data")
```

### 2. Secrets Management

```python
# Environment-based configuration ✅
import os
from dataclasses import dataclass

@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    api_key: str = os.getenv("API_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    
    def __post_init__(self):
        if not all([self.database_url, self.api_key, self.jwt_secret]):
            raise ValueError("Missing required environment variables")

# Alternative: Use python-dotenv for development
from dotenv import load_dotenv
load_dotenv()  # Loads .env file (never commit .env!)
```

### 3. Cryptography

```python
# Use established libraries ✅
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import base64

def generate_key_from_password(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))

# Secure password hashing ✅
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

### 4. Logging Security

```python
import logging
import re

# Secure logging configuration ✅
def setup_secure_logging():
    # Remove sensitive data from logs
    class SensitiveDataFilter(logging.Filter):
        def filter(self, record):
            # Remove common sensitive patterns
            sensitive_patterns = [
                r'password["\']?\s*[:=]\s*["\']?([^"\'\\s]+)',
                r'token["\']?\s*[:=]\s*["\']?([^"\'\\s]+)',
                r'key["\']?\s*[:=]\s*["\']?([^"\'\\s]+)',
            ]
            
            for pattern in sensitive_patterns:
                record.msg = re.sub(pattern, r'***REDACTED***', str(record.msg))
            return True
    
    logger = logging.getLogger()
    logger.addFilter(SensitiveDataFilter())
    return logger

# Usage ✅
logger = setup_secure_logging()
logger.info("User login successful")  # Good
logger.info(f"API key: {api_key}")     # Bad - will be redacted
```

## Infrastructure Security

### 1. Container Security

```dockerfile
# Dockerfile security best practices ✅
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
WORKDIR /app

# Switch to non-root user
USER appuser

# Use exec form for CMD
CMD ["python", "-m", "src.main"]
```

### 2. Environment Configuration

```bash
# Production environment variables
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PYTHONASYNCIODEBUG=0  # Disable in production
export PYTHONHASHSEED=random
```

## CI/CD Security Pipeline

### GitHub Actions Security Workflow

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety pip-audit
    
    - name: Run Bandit security scan
      run: |
        bandit -r src/ -f json -o bandit-report.json
        bandit -r src/ -ll  # Fail on high-confidence issues
    
    - name: Check dependencies for vulnerabilities
      run: |
        safety check --json --output safety-report.json
        pip-audit --format=json --output=pip-audit-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          pip-audit-report.json
```

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-x', 'tests/']
        exclude: ^tests/
  
  - repo: local
    hooks:
      - id: safety
        name: safety
        entry: safety
        args: ['check', '--json']
        language: python
        pass_filenames: false
```

## Monitoring and Response

### 1. Runtime Security Monitoring

```python
# Application security monitoring ✅
import logging
import time
from functools import wraps

def security_monitor(func):
    """Decorator to monitor security-sensitive operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log successful operations
            logging.info(f"Security operation {func.__name__} completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            # Log security failures
            logging.error(f"Security operation {func.__name__} failed: {str(e)}")
            raise
    
    return wrapper

@security_monitor
def authenticate_user(username: str, password: str):
    # Authentication logic here
    pass
```

### 2. Security Headers

```python
# FastAPI security headers ✅
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Security Checklist

### Development Phase
- [ ] Static analysis with Bandit integrated into development workflow
- [ ] Dependency vulnerability scanning with Safety/pip-audit
- [ ] Input validation using Pydantic or similar
- [ ] Secrets management through environment variables
- [ ] Secure logging configuration
- [ ] Code review process including security review

### Pre-deployment
- [ ] Container security scanning
- [ ] Dependency audit and updates
- [ ] Security headers configuration
- [ ] Environment hardening
- [ ] Backup and recovery procedures

### Production
- [ ] Runtime monitoring and alerting
- [ ] Regular security updates
- [ ] Incident response plan
- [ ] Security audit logs
- [ ] Performance monitoring for security anomalies

## Tools Summary

| Category | Tool | Purpose | Integration |
|----------|------|---------|-------------|
| **Static Analysis** | Bandit | Code vulnerability scanning | Pre-commit, CI/CD |
| **Dependencies** | Safety | Known vulnerability database | CI/CD, Scheduled |
| **Dependencies** | pip-audit | PyPA official scanner | Alternative to Safety |
| **Advanced** | Semgrep | Pattern-based analysis | CI/CD, Custom rules |
| **Containers** | Trivy | Container/image scanning | Docker builds |
| **Secrets** | GitLeaks | Prevent secret commits | Pre-commit hooks |

## Resources

- [OWASP Python Security Guide](https://owasp.org/www-project-python-security/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
- [PEP 578 - Python Runtime Audit Hooks](https://www.python.org/dev/peps/pep-0578/)

---

*This document is part of the Clean Architecture Python project. For implementation details, see the project's Makefile and CI/CD configuration.*