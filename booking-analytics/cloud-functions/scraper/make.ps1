# make.ps1 - PowerShell equivalent of Makefile for Web Scraper Project
# Usage: .\make.ps1 [command]
# or: powershell -ExecutionPolicy Bypass -File make.ps1 [command]

param(
    [string]$Command = "help",
    [string]$Test = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Variables
$PYTHON = "python"
$PIP = "pip"
$PYTEST = "pytest"
$DOCKER = "docker"

# Colors for output
function Write-Green { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Yellow { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Red { param($Message) Write-Host $Message -ForegroundColor Red }

# Function to check if dependencies are installed
function Test-Dependencies {
    Write-Green "Checking dependencies..."
    try {
        & $PYTHON -c "import flask, pytest, requests, google.cloud.storage" 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Dependencies missing"
        }
        Write-Green "✓ All dependencies installed"
        return $true
    }
    catch {
        Write-Red "✗ Missing dependencies. Run '.\make.ps1 install-dev'"
        return $false
    }
}

# Function to show help
function Show-Help {
    Write-Host ""
    Write-Green "Web Scraper Development Commands (PowerShell)"
    Write-Host ""
    Write-Yellow "Setup Commands:"
    Write-Host "  .\make.ps1 install          Install production dependencies"
    Write-Host "  .\make.ps1 install-dev      Install development dependencies"
    Write-Host "  .\make.ps1 setup            Complete project setup"
    Write-Host "  .\make.ps1 check-deps       Check if dependencies are installed"
    Write-Host ""
    Write-Yellow "Testing Commands:"
    Write-Host "  .\make.ps1 test             Run all tests"
    Write-Host "  .\make.ps1 test-verbose     Run tests with verbose output"
    Write-Host "  .\make.ps1 test-coverage    Run tests with coverage report"
    Write-Host "  .\make.ps1 test-coverage-html Generate HTML coverage report"
    Write-Host "  .\make.ps1 test-specific -Test TestName  Run specific test"
    Write-Host "  .\make.ps1 test-integration Run only integration tests"
    Write-Host "  .\make.ps1 test-unit        Run only unit tests"
    Write-Host "  .\make.ps1 test-parallel    Run tests in parallel"
    Write-Host ""
    Write-Yellow "Development Commands:"
    Write-Host "  .\make.ps1 lint             Run basic Python linting"
    Write-Host "  .\make.ps1 clean            Clean up generated files"
    Write-Host "  .\make.ps1 docker-build     Build Docker image"
    Write-Host "  .\make.ps1 docker-run       Run Docker container locally"
    Write-Host "  .\make.ps1 docker-test      Build and test Docker image"
    Write-Host "  .\make.ps1 status           Show project status"
    Write-Host ""
    Write-Yellow "Examples:"
    Write-Host "  .\make.ps1 setup            # Complete project setup"
    Write-Host "  .\make.ps1 test             # Run all tests"
    Write-Host "  .\make.ps1 test-coverage    # Run tests with coverage"
    Write-Host "  .\make.ps1 test-specific -Test TestLoadSourcesFromGCS"
    Write-Host ""
}

# Function to install production dependencies
function Install-Production {
    Write-Green "Installing production dependencies..."
    & $PIP install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Red "Error installing production dependencies"
        exit 1
    }
    Write-Green "✓ Production dependencies installed successfully"
}

# Function to install development dependencies
function Install-Development {
    Write-Green "Installing development dependencies..."
    Install-Production
    & $PIP install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Red "Error installing development dependencies"
        exit 1
    }
    Write-Green "✓ Development dependencies installed successfully"
}

# Function to setup project
function Setup-Project {
    Write-Green "Setting up project..."
    Install-Development
    Write-Green "Verifying setup..."
    & $PYTEST --version
    if ($LASTEXITCODE -ne 0) {
        Write-Red "Error: pytest not properly installed"
        exit 1
    }
    Write-Green "✓ Setup complete! Run '.\make.ps1 test' to run tests"
}

# Function to run tests
function Run-Tests {
    Write-Green "Running all tests..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST tests/
}

# Function to run tests with verbose output
function Run-TestsVerbose {
    Write-Green "Running tests with verbose output..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST -v tests/
}

# Function to run tests with coverage
function Run-TestsCoverage {
    Write-Green "Running tests with coverage..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST --cov=main --cov-report=term-missing tests/
}

# Function to generate HTML coverage report
function Run-TestsCoverageHtml {
    Write-Green "Generating HTML coverage report..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST --cov=main --cov-report=html tests/
    Write-Green "✓ Coverage report generated in htmlcov/index.html"
}

# Function to run specific test
function Run-TestSpecific {
    if (-not $Test) {
        Write-Red "Please specify test name. Example:"
        Write-Host "  .\make.ps1 test-specific -Test TestLoadSourcesFromGCS"
        exit 1
    }
    Write-Green "Running specific test: $Test"
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST -v "tests/test_main.py::$Test"
}

# Function to run integration tests
function Run-TestsIntegration {
    Write-Green "Running integration tests..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST -v tests/test_main.py::TestIntegration
}

# Function to run unit tests
function Run-TestsUnit {
    Write-Green "Running unit tests..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST -v tests/test_main.py -k "not TestIntegration"
}

# Function to run tests in parallel
function Run-TestsParallel {
    Write-Green "Running tests in parallel..."
    if (-not (Test-Dependencies)) { exit 1 }
    & $PYTEST -n auto tests/
}

# Function to run linting
function Run-Lint {
    Write-Green "Running basic Python syntax check..."
    & $PYTHON -m py_compile main.py
    if ($LASTEXITCODE -ne 0) {
        Write-Red "Python syntax check failed"
        exit 1
    }
    Write-Green "✓ Python syntax is valid"
}

# Function to clean up generated files
function Clean-Files {
    Write-Green "Cleaning up generated files..."
    
    # Remove directories if they exist
    $dirsToRemove = @("__pycache__", ".pytest_cache", "htmlcov", "dist", "build")
    foreach ($dir in $dirsToRemove) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Host "Removed: $dir"
        }
    }
    
    # Remove files if they exist
    $filesToRemove = @(".coverage")
    foreach ($file in $filesToRemove) {
        if (Test-Path $file) {
            Remove-Item -Force $file
            Write-Host "Removed: $file"
        }
    }
    
    # Remove egg-info directories
    Get-ChildItem -Directory -Name "*.egg-info" | ForEach-Object {
        Remove-Item -Recurse -Force $_
        Write-Host "Removed: $_"
    }
    
    # Remove Python cache files recursively
    Get-ChildItem -Recurse -Name "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
    
    Write-Green "✓ Cleanup complete"
}

# Function to build Docker image
function Build-Docker {
    Write-Green "Building Docker image..."
    & $DOCKER build -t scraper-app .
    if ($LASTEXITCODE -ne 0) {
        Write-Red "Docker build failed"
        exit 1
    }
    Write-Green "✓ Docker image built successfully"
}

# Function to run Docker container
function Run-Docker {
    Write-Green "Running Docker container..."
    & $DOCKER run -p 8080:8080 -e BUCKET_NAME=test-bucket scraper-app
}

# Function to test Docker image
function Test-Docker {
    Write-Green "Building and testing Docker image..."
    Build-Docker
    & $DOCKER run --rm scraper-app python -c "import main; print('✓ Docker image works')"
}

# Function to show project status
function Show-Status {
    Write-Host ""
    Write-Green "Project Status:"
    
    try {
        $pythonVersion = & $PYTHON --version 2>&1
        Write-Host "Python version: $pythonVersion"
    }
    catch {
        Write-Red "Python not found"
    }
    
    try {
        $pipVersion = & $PIP --version 2>&1
        Write-Host "Pip version: $pipVersion"
    }
    catch {
        Write-Red "Pip not found"
    }
    
    Write-Host "Working directory: $(Get-Location)"
    
    try {
        $packages = & $PIP list 2>$null | Select-String -Pattern "(flask|pytest|requests|google-cloud)"
        if ($packages) {
            Write-Host "Dependencies: Required packages appear to be installed"
        } else {
            Write-Host "Dependencies: Not all required packages installed"
        }
    }
    catch {
        Write-Red "Could not check dependencies"
    }
    
    Write-Host ""
    Write-Yellow "Available commands: Run '.\make.ps1 help' for detailed usage"
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Production }
    "install-dev" { Install-Development }
    "setup" { Setup-Project }
    "check-deps" { Test-Dependencies | Out-Null }
    "test" { Run-Tests }
    "test-verbose" { Run-TestsVerbose }
    "test-coverage" { Run-TestsCoverage }
    "test-coverage-html" { Run-TestsCoverageHtml }
    "test-specific" { Run-TestSpecific }
    "test-integration" { Run-TestsIntegration }
    "test-unit" { Run-TestsUnit }
    "test-parallel" { Run-TestsParallel }
    "lint" { Run-Lint }
    "clean" { Clean-Files }
    "docker-build" { Build-Docker }
    "docker-run" { Run-Docker }
    "docker-test" { Test-Docker }
    "status" { Show-Status }
    default {
        Write-Red "Unknown command: $Command"
        Show-Help
        exit 1
    }
} 