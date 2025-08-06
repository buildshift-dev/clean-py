# VS Code Problems Panel Management

This guide explains how to manage warnings, errors, and linting issues in VS Code's Problems panel, ensuring alignment between command line tools and the IDE experience.

## Overview

VS Code's Problems panel aggregates issues from multiple sources:
- **Ruff extension** (linting & formatting)
- **Pylint extension** (code quality)  
- **Pyright/Pylance** (type checking)
- **Python extension** (general Python support)

## Problems Panel Controls

### Quick Filtering
1. **Filter Icon**: Click the filter button in Problems panel
   - Uncheck "Warnings" to hide all warnings
   - Uncheck "Infos" to hide informational messages
   - Keep "Errors" for critical issues only

2. **Filter Box**: Use text patterns to filter
   - `!pylint` - Hide all pylint messages
   - `unnecessary` - Show only "unnecessary" warnings
   - `@type:warning` - Show only warnings

3. **View Options**:
   - **Tree View**: Group by file
   - **Table View**: Flat list of all issues
   - **Current File Only**: Toggle in status bar

## Configuration Strategies

### 1. Tool-Specific Configuration

#### Ruff Configuration
Configure in `pyproject.toml` (affects both CLI and VS Code):
```toml
[tool.ruff.lint]
ignore = [
    "E501",   # Line too long (handled by formatter)
    "W0107",  # Unnecessary pass statement
    "C0301",  # Line too long (pylint)
]
```

#### Pylint Configuration  
In workspace settings or `pyproject.toml`:
```json
{
  "python.linting.pylintArgs": [
    "--disable=C0301,R0902,R0913,W0107,W0212",
    "--fail-under=9.0"
  ]
}
```

#### Pyright/Pylance Configuration
In workspace settings:
```json
{
  "python.analysis.diagnosticSeverityOverrides": {
    "reportUnnecessaryIsInstance": "none",
    "reportImplicitStringConcatenation": "warning",
    "reportUnusedImport": "error"
  }
}
```

### 2. Workspace vs User Settings

#### Workspace Settings (`.code-workspace` or `.vscode/settings.json`)
```json
{
  "settings": {
    // Apply to this project only
    "python.analysis.diagnosticMode": "openFilesOnly",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    
    // Control problem reporting
    "problems.decorations.enabled": true,
    "problems.defaultViewMode": "tree"
  }
}
```

#### User Settings (Global)
- `Ctrl/Cmd + ,` → Search specific settings
- Affects all VS Code Python projects

### 3. Severity Overrides

Control what shows as error vs warning vs info:

```json
{
  "python.analysis.diagnosticSeverityOverrides": {
    // Hide completely
    "reportUnnecessaryIsInstance": "none",
    
    // Downgrade from error to warning  
    "reportMissingImports": "warning",
    
    // Upgrade from warning to error
    "reportUnusedVariable": "error"
  }
}
```

## Best Practices

### 1. Align Command Line and VS Code
Ensure your `make pre-commit` and VS Code show the same issues:

```bash
# Test alignment
source .venv/bin/activate
ruff check src/domain/entities/customer.py    # Should match VS Code Ruff issues
pylint src/domain/entities/customer.py        # Should match VS Code Pylint issues  
pyright src/domain/entities/customer.py       # Should match VS Code type issues
```

### 2. Configure Once, Use Everywhere
- Put tool configuration in `pyproject.toml` when possible
- Use workspace settings for VS Code-specific behavior
- Avoid per-file `# pylint: disable` comments

### 3. Manage Noise vs Signal
- **Errors**: Always fix (breaks functionality)
- **Warnings**: Configure away if they don't add value to your project
- **Info**: Usually safe to hide in Problems panel

### 4. Team Consistency
Document your project's approach:
```json
{
  // Project standard: Hide design warnings but show code quality issues
  "python.linting.pylintArgs": [
    "--disable=R0902,R0913,R0917",  // Design warnings  
    "--enable=C,W,E,F"              // Code quality issues
  ]
}
```

## Common Warning Categories

### Safe to Hide (Usually)
- `R0902` - Too many instance attributes (DDD entities often have many)
- `R0913` - Too many arguments (some constructors need them)
- `W0107` - Unnecessary pass (abstract methods)
- `W0212` - Protected access (domain events pattern)

### Keep Visible (Recommended)
- `E****` - Error conditions
- `F401` - Unused imports  
- `W0613` - Unused arguments
- Type checking errors

### Project-Specific
- `C0301` - Line too long (if you use auto-formatters)
- `S101` - Assert statements (if you use them in tests)

## Diagnostic Modes

Control when problems are reported:

```json
{
  // Only analyze open files (faster, less comprehensive)
  "python.analysis.diagnosticMode": "openFilesOnly",
  
  // Analyze entire workspace (slower, more thorough)  
  "python.analysis.diagnosticMode": "workspace"
}
```

## Troubleshooting

### Problems Don't Match CLI
1. Check VS Code is using your virtual environment
2. Verify tool versions: `pip list | grep -E "ruff|pylint"`
3. Reload VS Code window: `Developer: Reload Window`

### Too Many Warnings
1. Start with errors only: Filter out warnings temporarily
2. Configure tools to reduce noise
3. Gradually re-enable warnings that add value

### Missing Issues
1. Check if linting is enabled: `Python: Enable/Disable Linting`
2. Verify extensions are installed and enabled
3. Check output panel for extension errors

## Example Configuration

For this project's approach (Clean Architecture + DDD):

```json
{
  "settings": {
    // Show problems for open files only (performance)
    "python.analysis.diagnosticMode": "openFilesOnly",
    
    // Hide DDD-pattern related warnings
    "python.linting.pylintArgs": [
      "--disable=R0902,R0913,R0917,W0212",
      "--fail-under=9.0"
    ],
    
    // Keep type checking strict but hide unnecessary isinstance
    "python.analysis.diagnosticSeverityOverrides": {
      "reportUnnecessaryIsInstance": "none"
    },
    
    // Problems panel preferences
    "problems.defaultViewMode": "tree",
    "problems.decorations.enabled": true
  }
}
```

This configuration prioritizes code correctness while reducing noise from architectural pattern choices.

## Code Tidiness Management

Beyond fixing errors and warnings, VS Code can automatically maintain code cleanliness and consistency.

### Auto-Formatting on Save

Configure automatic code formatting:

```json
{
  "settings": {
    // Enable format on save
    "[python]": {
      "editor.defaultFormatter": "charliermarsh.ruff",
      "editor.formatOnSave": true,
      "editor.formatOnType": false,
      "editor.formatOnPaste": true
    },
    
    // Code actions on save
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",           // Fix all ruff issues
      "source.organizeImports.ruff": "explicit",  // Sort/organize imports
      "source.fixAll": "never"                    // Disable other auto-fixes
    }
  }
}
```

### Import Management

Keep imports clean and organized:

```json
{
  "settings": {
    // Ruff handles import sorting (replaces isort)
    "ruff.organizeImports": true,
    
    // Remove unused imports on save
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    },
    
    // Pyright: auto-import completions
    "python.analysis.autoImportCompletions": true,
    "python.analysis.completeFunctionParens": true
  }
}
```

### File and Workspace Tidiness

```json
{
  "settings": {
    // Trim whitespace automatically
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,
    
    // Editor appearance
    "editor.rulers": [88],                    // Show line length guide
    "editor.renderWhitespace": "boundary",    // Show excess whitespace
    "editor.guides.bracketPairs": true,       // Bracket pair guides
    
    // File exclusions (keep workspace clean)
    "files.exclude": {
      "**/__pycache__": true,
      "**/*.pyc": true,
      ".pytest_cache": true,
      ".mypy_cache": true,
      ".ruff_cache": true,
      "**/.DS_Store": true
    }
  }
}
```

### Code Quality Helpers

Extensions and settings that maintain code quality:

```json
{
  "settings": {
    // Highlight TODO/FIXME comments
    "todo-tree.general.tags": ["TODO", "FIXME", "HACK", "NOTE"],
    
    // Bracket colorization
    "editor.bracketPairColorization.enabled": true,
    "editor.guides.bracketPairs": "active",
    
    // Indent guides
    "editor.guides.indentation": true,
    
    // Word wrap for long lines
    "editor.wordWrap": "wordWrapColumn",
    "editor.wordWrapColumn": 88
  }
}
```

### Automatic Code Actions

Configure what gets fixed automatically:

```json
{
  "settings": {
    "editor.codeActionsOnSave": {
      // Ruff fixes (safe auto-fixes only)
      "source.fixAll.ruff": "explicit",
      
      // Import organization
      "source.organizeImports.ruff": "explicit",
      
      // Remove unused variables (careful - may break code)
      "source.unusedImports": "never",
      
      // Add missing imports
      "source.addMissingImports": "explicit"
    }
  }
}
```

### File Organization Best Practices

#### 1. Consistent File Structure
```
src/
├── domain/          # Core business logic
├── application/     # Use cases
├── infrastructure/  # External concerns
├── presentation/    # API/UI layer
└── shared_kernel/   # Common utilities
```

#### 2. Import Organization (handled by ruff)
```python
# Standard library imports
from datetime import datetime
from typing import Optional

# Third-party imports  
from pydantic import BaseModel

# Local application imports
from src.domain.entities.customer import Customer
from src.shared_kernel import CustomerId
```

#### 3. Code Formatting Standards
```json
{
  "[python]": {
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.detectIndentation": false
  }
}
```

### Tidiness Automation Tools

#### Essential Extensions
1. **Ruff** (`charliermarsh.ruff`) - Linting + formatting
2. **Pylint** (`ms-python.pylint`) - Code quality
3. **Python** (`ms-python.python`) - Core Python support
4. **Todo Tree** (`gruntfuggly.todo-tree`) - Track TODO comments

#### Optional Tidiness Extensions
1. **Auto Rename Tag** - Keep HTML/XML tags in sync
2. **Bracket Pair Colorizer** - Color-code brackets
3. **GitLens** - Git blame and history
4. **Path Intellisense** - Autocomplete file paths

### Workspace Tidiness Commands

Add custom commands for tidiness:

```json
{
  "tasks": {
    "version": "2.0.0",
    "tasks": [
      {
        "label": "Clean Code",
        "type": "shell",
        "command": "make",
        "args": ["format", "lint"],
        "group": "build",
        "presentation": {
          "echo": true,
          "reveal": "always"
        }
      }
    ]
  }
}
```

### Pre-commit Integration

Ensure tidiness before commits:

```json
{
  "settings": {
    // Git settings
    "git.enableSmartCommit": true,
    "git.confirmSync": false,
    
    // Run pre-commit hooks
    "git.useCommitInputAsStashMessage": true,
    
    // Show git decorations
    "scm.decorations.enabled": true
  }
}
```

### Code Tidiness Checklist

#### Daily Habits
- [ ] Format on save is enabled
- [ ] Import organization on save
- [ ] Remove trailing whitespace
- [ ] Check for TODO comments before committing

#### Weekly Maintenance  
- [ ] Run `make clean` to remove cache files
- [ ] Review and organize imports across modules
- [ ] Check for unused dependencies in `requirements.txt`
- [ ] Update code documentation

#### Code Review Standards
- [ ] Consistent naming conventions
- [ ] Proper type hints
- [ ] Clear function/class documentation
- [ ] No commented-out code
- [ ] Logical import organization

### Troubleshooting Tidiness Issues

#### Formatting Not Working
1. Check default formatter: `Python: Select Interpreter`
2. Verify ruff extension is enabled
3. Check `editor.defaultFormatter` setting

#### Imports Not Organizing
1. Ensure `source.organizeImports.ruff` is enabled
2. Check ruff configuration in `pyproject.toml`
3. Manual trigger: `Python: Sort Imports`

#### Cache Issues
```bash
# Clean up caches that can cause issues
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".ruff_cache" -exec rm -rf {} +
```

This comprehensive approach ensures your codebase stays clean, consistent, and maintainable automatically.