# VS Code Test Discovery Guide

## Prerequisites

1. **Activate your virtual environment**
   ```bash
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate  # Windows
   ```

2. **Run the development setup**
   ```bash
   make setup-dev
   # This installs dependencies and sets up editable package installation
   ```

3. **Open VS Code using the workspace file**
   ```bash
   code clean-py.code-workspace
   ```

## Enabling Test Discovery

### Method 1: Using Command Palette (Recommended)

1. Open Command Palette: `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type: "Python: Configure Tests"
3. Select: "pytest"
4. Select: "tests" folder
5. VS Code will discover all tests

### Method 2: Using Testing Sidebar

1. Click the Testing icon in the Activity Bar (flask icon)
2. Click "Configure Python Tests" if prompted
3. Select "pytest" and "tests" folder

### Method 3: Manual Refresh

1. Open Command Palette: `Cmd+Shift+P` or `Ctrl+Shift+P`
2. Run: "Python: Discover Tests"

## Verifying Test Discovery

Once configured, you should see:

1. **Testing sidebar** shows test hierarchy:
   ```
   tests/
   ├── unit/
   │   ├── application/
   │   │   ├── test_create_customer.py
   │   │   │   └── TestCreateCustomerUseCase
   │   │   │       ├── test_create_customer_success ✓
   │   │   │       ├── test_create_customer_duplicate_email ✓
   │   │   │       └── test_create_customer_with_empty_preferences ✓
   │   │   └── test_create_order.py
   │   │       └── TestCreateOrderUseCase
   │   │           ├── test_create_order_success ✓
   │   │           └── ...
   │   └── domain/
   │       ├── test_customer.py
   │       └── test_order.py
   ```

2. **Inline test buttons** in code files:
   - Green play button: Run single test
   - Bug icon: Debug single test

3. **Test status indicators**:
   - ✓ Passed tests (green)
   - ✗ Failed tests (red)
   - ⚠ Skipped tests (yellow)

## Running Tests in VS Code

### Run All Tests
- Click the "Run All Tests" button in Testing sidebar
- Or use Command Palette: "Python: Run All Tests"

### Run Single Test
- Click the play button next to the test in:
  - Testing sidebar
  - Code editor (inline button)

### Debug Test
- Click the bug icon next to the test
- Set breakpoints in your code
- Step through execution

### Run Test File
- Right-click test file in Testing sidebar
- Select "Run Tests"

### Run Test Class
- Click play button next to test class name

## Troubleshooting Test Discovery

### Tests Not Discovered?

1. **Check Python interpreter**
   ```bash
   # In VS Code terminal
   which python
   # Should show: /path/to/project/.venv/bin/python
   ```

2. **Select correct interpreter**
   - Command Palette: "Python: Select Interpreter"
   - Choose: `./.venv/bin/python`

3. **Verify editable installation**
   ```bash
   pip list | grep clean-py
   # Should show: clean-py    0.1.0    /path/to/clean-py
   ```

4. **Check test configuration**
   - Open `.vscode/settings.json` or workspace file
   - Ensure `python.testing.pytestEnabled` is `true`

5. **Clear VS Code cache**
   - Command Palette: "Python: Clear Cache and Reload Window"

### Import Errors?

If tests fail with `ModuleNotFoundError: No module named 'src'`:

```bash
# Ensure you're in the project root
cd /path/to/clean-py

# Activate virtual environment
source .venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

### Tests Run in Terminal but Not VS Code?

1. Check output panel:
   - View → Output → Python Test Log
   - Look for error messages

2. Ensure pytest is installed in venv:
   ```bash
   .venv/bin/pip install pytest pytest-asyncio
   ```

## Test Output and Results

### View Test Output
- Click on a test result in Testing sidebar
- Output appears in "Test Results" panel
- Shows full pytest output including prints

### Test Coverage
To see coverage in VS Code:

1. Install coverage extension: "Coverage Gutters"
2. Run tests with coverage:
   ```bash
   make test-coverage
   ```
3. Command Palette: "Coverage Gutters: Display Coverage"

## Keyboard Shortcuts

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Run all tests | `Cmd+Shift+T` | `Ctrl+Shift+T` |
| Debug test at cursor | `F5` (with cursor on test) | `F5` |
| Run test at cursor | Place cursor on test, click play button | Same |

## Best Practices

1. **Keep tests fast**: Unit tests should run in < 1 second
2. **Use test markers**: `@pytest.mark.slow` for integration tests
3. **Clear test names**: `test_should_do_something_when_condition`
4. **One assertion per test**: Makes failures clear
5. **Use fixtures**: For common test setup

## Configuration Files

The test discovery is configured in:

1. **`.vscode/settings.json`**: Project-level VS Code settings
2. **`clean-py.code-workspace`**: Workspace settings
3. **`pyproject.toml`**: pytest configuration
4. **`.venv/`**: Virtual environment with dependencies

---

*Last updated: 2025-08-02*