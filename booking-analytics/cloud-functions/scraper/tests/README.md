# Testing Guide

This directory contains comprehensive tests for the web scraper application.

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Make sure your main dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run specific test class
pytest tests/test_main.py::TestLoadSourcesFromGCS

# Run specific test method
pytest tests/test_main.py::TestLoadSourcesFromGCS::test_load_sources_success
```

### Coverage Reports
```bash
# Run tests with coverage
pytest --cov=main

# Generate HTML coverage report
pytest --cov=main --cov-report=html
# Open htmlcov/index.html in browser to view detailed coverage

# Coverage with missing lines
pytest --cov=main --cov-report=term-missing
```

### Parallel Execution (faster)
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Structure

### `conftest.py`
- Shared fixtures and test configuration
- Flask test client setup
- Mock data for testing

### `test_main.py`
Contains test classes for each component:

- **TestLoadSourcesFromGCS**: Tests GCS configuration loading
- **TestUploadResultToGCS**: Tests data persistence to GCS  
- **TestFetchHTMLWithRetries**: Tests HTTP scraping with retry logic
- **TestFlaskRoutes**: Tests API endpoints
- **TestIntegration**: End-to-end integration tests

## Understanding Test Output

### Successful Run
```
========================= test session starts =========================
collected 15 items

tests/test_main.py::TestLoadSourcesFromGCS::test_load_sources_success PASSED
tests/test_main.py::TestLoadSourcesFromGCS::test_load_sources_file_not_found PASSED
...
========================= 15 passed in 2.34s =========================
```

### Failed Test
```
FAILED tests/test_main.py::TestLoadSourcesFromGCS::test_load_sources_success
```
Check the detailed error output to understand what went wrong.

## Mocking Strategy

Tests use extensive mocking to avoid:
- Making real HTTP requests
- Connecting to actual GCS buckets
- Depending on external services

This makes tests:
- Fast (run in seconds)
- Reliable (no network dependencies)
- Safe (no real cloud resources used)

## Adding New Tests

When adding new functionality:

1. Add test fixtures to `conftest.py` if reusable
2. Add test methods to appropriate test class in `test_main.py`
3. Follow naming convention: `test_function_name_scenario`
4. Include docstrings explaining the test purpose
5. Mock external dependencies

## Common Issues

### Import Errors
If you get import errors, make sure you're running pytest from the project root:
```bash
# From the scraper/ directory (where main.py is)
pytest tests/
```

### Mock Issues
If mocks aren't working as expected, check:
- Patch paths are correct (`main.storage.Client` not `storage.Client`)
- Mock return values match expected data types
- Mock call counts match your expectations 