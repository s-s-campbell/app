# Development Guide

This guide helps you set up and work with the web scraper locally, including development tools, testing, and deployment workflows.

## 📋 Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud` CLI)
- Git
- Make (Linux/Mac) or PowerShell (Windows)

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone your repository
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Set up environment variables (REQUIRED)
export BUCKET_NAME="sports-booking-webscraper"
export PROJECT_ID="sports-booking-465210"

# For Windows PowerShell:
$env:BUCKET_NAME="sports-booking-webscraper"
$env:PROJECT_ID="sports-booking-465210"
```

### 2. Install Dependencies

```bash
# Install production dependencies
make install

# Install development dependencies (for testing/linting)
make install-dev

# Or do both at once
make setup
```

## 🔐 Security Configuration

⚠️ **Important**: The application now requires environment variables for security. See `SECURITY.md` for complete security guidelines.

### Required Environment Variables
```bash
# Required for the application to start
export BUCKET_NAME="sports-booking-webscraper"

# Optional but recommended
export PROJECT_ID="sports-booking-465210"
```

### Local Development Security
```bash
# For testing with different environments
export BUCKET_NAME="dev-sports-booking-webscraper"
export PROJECT_ID="dev-sports-booking-project"
```

**Security Note**: Never hardcode credentials in source code. Use environment variables or Google Cloud Secret Manager for sensitive data.

## 🚀 Quick Start

### Linux/Mac Users
```bash
# Setup project
make setup

# Run tests
make test

# Run tests with coverage
make test-coverage
```

### Windows Users (Command Prompt)
```cmd
REM Setup project
make.bat setup

REM Run tests
make.bat test

REM Run tests with coverage
make.bat test-coverage
```

### Windows Users (PowerShell)
```powershell
# Setup project
.\make.ps1 setup

# Run tests
.\make.ps1 test

# Run tests with coverage
.\make.ps1 test-coverage
```

## 📋 Available Commands

All platforms support the same commands, just with different syntax:

| Command | Linux/Mac | Windows Batch | Windows PowerShell |
|---------|-----------|---------------|-------------------|
| Show help | `make help` | `make.bat help` | `.\make.ps1 help` |
| Setup project | `make setup` | `make.bat setup` | `.\make.ps1 setup` |
| Run tests | `make test` | `make.bat test` | `.\make.ps1 test` |
| Build Docker | `make docker-build` | `make.bat docker-build` | `.\make.ps1 docker-build` |

### 🔧 Setup Commands

- **`install`** - Install production dependencies only
- **`install-dev`** - Install development dependencies (includes production)
- **`setup`** - Complete project setup (recommended for first-time setup)
- **`check-deps`** - Verify all dependencies are installed

### 🧪 Testing Commands

- **`test`** - Run all tests
- **`test-verbose`** - Run tests with detailed output
- **`test-coverage`** - Run tests with coverage report
- **`test-coverage-html`** - Generate HTML coverage report
- **`test-specific`** - Run a specific test class or method
- **`test-integration`** - Run only integration tests
- **`test-unit`** - Run only unit tests (excludes integration)
- **`test-parallel`** - Run tests in parallel (faster)

### 🛠️ Development Commands

- **`lint`** - Run basic Python syntax checking
- **`clean`** - Clean up generated files and cache
- **`docker-build`** - Build Docker image
- **`docker-run`** - Run Docker container locally
- **`docker-test`** - Build and test Docker image
- **`status`** - Show project status and configuration

## 📖 Detailed Usage Examples

### Initial Project Setup

**First time setting up the project:**
```bash
# Linux/Mac
make setup

# Windows Command Prompt
make.bat setup

# Windows PowerShell
.\make.ps1 setup
```

This will:
1. Install all dependencies (production + development)
2. Verify pytest is working
3. Confirm setup is complete

### Running Specific Tests

**Run a specific test class:**
```bash
# Linux/Mac
make test-specific TEST=TestLoadSourcesFromGCS

# Windows Command Prompt
set TEST=TestLoadSourcesFromGCS
make.bat test-specific

# Windows PowerShell
.\make.ps1 test-specific -Test TestLoadSourcesFromGCS
```

**Run a specific test method:**
```bash
# Linux/Mac
make test-specific TEST=TestLoadSourcesFromGCS::test_load_sources_success

# Windows Command Prompt
set TEST=TestLoadSourcesFromGCS::test_load_sources_success
make.bat test-specific

# Windows PowerShell
.\make.ps1 test-specific -Test "TestLoadSourcesFromGCS::test_load_sources_success"
```

### Coverage Reports

**Terminal coverage report:**
```bash
make test-coverage        # Linux/Mac
make.bat test-coverage    # Windows CMD
.\make.ps1 test-coverage  # Windows PS
```

**HTML coverage report:**
```bash
make test-coverage-html        # Linux/Mac
make.bat test-coverage-html    # Windows CMD
.\make.ps1 test-coverage-html  # Windows PS
```

The HTML report will be generated in `htmlcov/index.html` - open this in your browser for detailed coverage analysis.

### Docker Development

**Build and test Docker image:**
```bash
# Build image
make docker-build        # Linux/Mac
make.bat docker-build    # Windows CMD
.\make.ps1 docker-build  # Windows PS

# Test the built image
make docker-test        # Linux/Mac
make.bat docker-test    # Windows CMD
.\make.ps1 docker-test  # Windows PS

# Run container locally
make docker-run        # Linux/Mac
make.bat docker-run    # Windows CMD
.\make.ps1 docker-run  # Windows PS
```

### Cleaning Up

**Remove generated files:**
```bash
make clean        # Linux/Mac
make.bat clean    # Windows CMD
.\make.ps1 clean  # Windows PS
```

This removes:
- Python cache files (`__pycache__`, `*.pyc`)
- Test artifacts (`.pytest_cache`, `.coverage`)
- Build artifacts (`dist/`, `build/`, `*.egg-info/`)
- Coverage reports (`htmlcov/`)

## 🔍 Troubleshooting

### Common Issues

**1. "Command not found" errors:**
- Make sure Python and pip are in your PATH
- On Windows, you might need to use `python` instead of `python3`
- Try running commands with full paths

**2. Permission errors on Windows:**
- Run Command Prompt or PowerShell as Administrator
- For PowerShell, you might need to set execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

**3. Dependency installation fails:**
- Make sure you have an active internet connection
- Try upgrading pip: `pip install --upgrade pip`
- Check if you're in a virtual environment

**4. Tests fail with import errors:**
- Run `make check-deps` to verify dependencies
- Make sure you're in the correct directory (where `main.py` is)
- Try `make clean` followed by `make setup`

### Getting Help

**Check project status:**
```bash
make status        # Linux/Mac
make.bat status    # Windows CMD
.\make.ps1 status  # Windows PS
```

**Show all available commands:**
```bash
make help        # Linux/Mac
make.bat help    # Windows CMD
.\make.ps1 help  # Windows PS
```

## 🎯 Development Workflow

### Recommended Development Flow

1. **Initial setup:**
   ```bash
   make setup
   ```

2. **Before making changes:**
   ```bash
   make test-coverage  # Ensure all tests pass
   ```

3. **After making changes:**
   ```bash
   make test           # Quick test run
   make lint           # Check syntax
   ```

4. **Before committing:**
   ```bash
   make test-coverage  # Full test with coverage
   make clean          # Clean up artifacts
   ```

5. **Before deploying:**
   ```bash
   make docker-test    # Test Docker build
   ```

### Continuous Integration

For CI/CD pipelines, use these commands:
```bash
make ci-install     # Install dependencies
make ci-test        # Run tests with coverage
make ci-build       # Build Docker image
```

## 📚 Additional Resources

- **Test Documentation**: See `tests/README.md` for detailed testing information
- **Docker Documentation**: See `Dockerfile` and `.dockerignore` for container configuration
- **Dependencies**: See `requirements.txt` (production) and `requirements-dev.txt` (development)

## 💡 Tips

1. **Use tab completion** - Most shells support tab completion for make targets
2. **Parallel testing** - Use `test-parallel` for faster test runs during development
3. **Watch mode** - Some versions support `test-watch` for continuous testing
4. **IDE integration** - Many IDEs can run these make commands directly
5. **Custom aliases** - Create shell aliases for frequently used commands 