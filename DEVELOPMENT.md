# Development Setup

This document explains how to set up the development environment and use the automated testing and linting tools.

## Pre-commit Hooks Setup

The project uses pre-commit hooks to automatically test and lint code before each commit to ensure code quality.

### Installation

1. **Install development dependencies:**
   ```bash
   uv sync --group dev
   ```

2. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type pre-push
   ```

3. **Or use the Makefile:**
   ```bash
   make dev-install
   make setup-hooks
   ```

### What Gets Checked

The pre-commit hooks run the following checks **before each commit**:

1. **Code Formatting:**
   - **trailing-whitespace**: Removes trailing whitespace
   - **end-of-file-fixer**: Ensures files end with newline
   - **Black**: Python code formatter
   - **Ruff**: Fast Python linter with auto-fix

2. **File Validation:**
   - **check-yaml**: YAML syntax validation
   - **check-json**: JSON syntax validation
   - **check-toml**: TOML syntax validation
   - **check-merge-conflict**: Detects merge conflict markers
   - **check-added-large-files**: Prevents accidentally committing large files
   - **detect-private-key**: Detects private keys in commits

3. **Type Checking:**
   - **MyPy**: Static type checking (warnings only, won't block commits)

4. **Testing:**
   - **pytest**: Runs all tests before commit
   - **pytest-changed**: Runs tests before push

### Manual Commands

You can run these checks manually:

```bash
# Run all pre-commit hooks on all files
make pre-commit

# Run specific checks
make format          # Black formatting
make lint           # Ruff linting + MyPy
make test           # Run tests
make test-cov       # Run tests with coverage

# Run all quality checks
make quality        # format + lint + test
```

### Skipping Hooks

If you need to skip pre-commit hooks (not recommended):

```bash
# Skip all pre-commit hooks
git commit --no-verify -m "commit message"

# Skip specific hooks
SKIP=mypy git commit -m "commit message"
```

### GitHub Actions Integration

The same checks run automatically on GitHub when you:

- Push to `main` or `develop` branches
- Create pull requests

Two workflows are configured:

1. **CI Workflow** (`.github/workflows/ci.yml`):
   - Tests on Python 3.10, 3.11, 3.12
   - Runs linting, formatting checks, type checking, and tests
   - Uploads coverage reports

2. **Pre-commit Workflow** (`.github/workflows/pre-commit.yml`):
   - Runs the same pre-commit hooks as locally
   - Ensures consistency between local and CI environments

### Configuration Files

- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration
- **`pyproject.toml`**: Tool configurations (Black, Ruff, MyPy, pytest)
- **`Makefile`**: Development convenience commands

### Troubleshooting

**Pre-commit hooks fail locally:**
```bash
# Update pre-commit hooks
uv run pre-commit autoupdate

# Run hooks on all files to see issues
uv run pre-commit run --all-files

# Clear pre-commit cache if needed
uv run pre-commit clean
```

**Tests fail:**
```bash
# Run tests with verbose output
uv run python -m pytest -v

# Run specific test
uv run python -m pytest tests/test_feeds.py -v
```

**Linting errors:**
```bash
# Auto-fix most linting issues
uv run ruff check src/ tests/ --fix

# Format code
uv run black src/ tests/
```

### Development Workflow

1. **Make your changes**
2. **Run quality checks:** `make quality`
3. **Commit your changes:** `git commit -m "your message"`
   - Pre-commit hooks will run automatically
   - If hooks fail, fix the issues and commit again
4. **Push to GitHub:** `git push`
   - Additional tests will run on GitHub Actions

This setup ensures that:
- Code is consistently formatted
- Linting rules are enforced
- Tests pass before code is committed
- Type hints are checked (warnings only)
- No sensitive data is accidentally committed

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run python -m pytest tests/test_feeds.py

# Run RSS feed tests only
make test-feeds
```

### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **Feed Tests**: Test RSS/Atom feed functionality

### Coverage Reports

Coverage reports are generated in `htmlcov/` directory when using `make test-cov`.

## Code Quality

The project maintains high code quality standards through:

- **Automated formatting** with Black
- **Linting** with Ruff (replaces flake8, isort, etc.)
- **Type checking** with MyPy
- **Testing** with pytest
- **Pre-commit hooks** for consistency
- **GitHub Actions** for CI/CD

This ensures that all code is:
- Consistently formatted
- Free of common errors
- Well-tested
- Type-safe (where possible)
- Secure
