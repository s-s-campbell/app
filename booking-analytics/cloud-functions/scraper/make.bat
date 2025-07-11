@echo off
REM make.bat - Windows equivalent of Makefile for Web Scraper Project
REM Usage: make.bat [command]

setlocal enabledelayedexpansion

REM Set variables
set PYTHON=python
set PIP=pip
set PYTEST=pytest
set DOCKER=docker

REM Test environment variables
set TEST_BUCKET_NAME=test-bucket-for-testing
set TEST_PROJECT_ID=test-project-for-testing

REM Colors (if supported)
set GREEN=[32m
set YELLOW=[33m
set RED=[31m
set NC=[0m

REM Check if command line argument provided
if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="install-dev" goto install_dev
if "%1"=="setup" goto setup
if "%1"=="check-deps" goto check_deps
if "%1"=="test" goto test
if "%1"=="test-verbose" goto test_verbose
if "%1"=="test-coverage" goto test_coverage
if "%1"=="test-coverage-html" goto test_coverage_html
if "%1"=="test-specific" goto test_specific
if "%1"=="test-integration" goto test_integration
if "%1"=="test-unit" goto test_unit
if "%1"=="test-parallel" goto test_parallel
if "%1"=="lint" goto lint
if "%1"=="clean" goto clean
if "%1"=="docker-build" goto docker_build
if "%1"=="docker-run" goto docker_run
if "%1"=="docker-test" goto docker_test
if "%1"=="status" goto status
echo Unknown command: %1
goto help

:help
echo.
echo Web Scraper Development Commands (Windows)
echo.
echo Setup Commands:
echo   make.bat install          Install production dependencies
echo   make.bat install-dev      Install development dependencies
echo   make.bat setup            Complete project setup
echo   make.bat check-deps       Check if dependencies are installed
echo.
echo Testing Commands:
echo   make.bat test             Run all tests
echo   make.bat test-verbose     Run tests with verbose output
echo   make.bat test-coverage    Run tests with coverage report
echo   make.bat test-coverage-html Generate HTML coverage report
echo   make.bat test-specific    Run specific test ^(set TEST=testname first^)
echo   make.bat test-integration Run only integration tests
echo   make.bat test-unit        Run only unit tests
echo   make.bat test-parallel    Run tests in parallel
echo.
echo Development Commands:
echo   make.bat lint             Run basic Python linting
echo   make.bat clean            Clean up generated files
echo   make.bat docker-build     Build Docker image
echo   make.bat docker-run       Run Docker container locally
echo   make.bat docker-test      Build and test Docker image
echo   make.bat status           Show project status
echo.
echo Examples:
echo   make.bat setup            # Complete project setup
echo   make.bat test             # Run all tests
echo   make.bat test-coverage    # Run tests with coverage
echo   set TEST=TestLoadSourcesFromGCS ^& make.bat test-specific
echo.
echo Note: Tests use test environment variables for safety
echo   BUCKET_NAME=%TEST_BUCKET_NAME%
echo   PROJECT_ID=%TEST_PROJECT_ID%
echo.
goto end

:install
echo Installing production dependencies...
%PIP% install -r requirements.txt
if errorlevel 1 (
    echo Error installing production dependencies
    exit /b 1
)
echo Production dependencies installed successfully
goto end

:install_dev
echo Installing development dependencies...
call :install
%PIP% install -r requirements-dev.txt
if errorlevel 1 (
    echo Error installing development dependencies
    exit /b 1
)
echo Development dependencies installed successfully
goto end

:setup
echo Setting up project...
call :install_dev
echo Verifying setup...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% --version
if errorlevel 1 (
    echo Error: pytest not properly installed
    exit /b 1
)
echo Setup complete! Run 'make.bat test' to run tests
goto end

:check_deps
echo Checking dependencies...
%PYTHON% -c "import flask, pytest, requests, google.cloud.storage" 2>nul
if errorlevel 1 (
    echo Missing dependencies. Run 'make.bat install-dev'
    exit /b 1
)
echo All dependencies installed
goto end

:test
echo Running all tests...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% tests/
goto end

:test_verbose
echo Running tests with verbose output...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% -v tests/
goto end

:test_coverage
echo Running tests with coverage...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% --cov=main --cov-report=term-missing tests/
goto end

:test_coverage_html
echo Generating HTML coverage report...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% --cov=main --cov-report=html tests/
echo Coverage report generated in htmlcov/index.html
goto end

:test_specific
if "%TEST%"=="" (
    echo Please set TEST variable first. Example:
    echo set TEST=TestLoadSourcesFromGCS
    echo make.bat test-specific
    exit /b 1
)
echo Running specific test: %TEST%
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% -v tests/test_main.py::%TEST%
goto end

:test_integration
echo Running integration tests...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% -v tests/test_main.py::TestIntegration
goto end

:test_unit
echo Running unit tests...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% -v tests/test_main.py -k "not TestIntegration"
goto end

:test_parallel
echo Running tests in parallel...
call :check_deps
if errorlevel 1 exit /b 1
echo Setting test environment variables...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTEST% -n auto tests/
goto end

:lint
echo Running basic Python syntax check...
set BUCKET_NAME=%TEST_BUCKET_NAME%
set PROJECT_ID=%TEST_PROJECT_ID%
%PYTHON% -m py_compile main.py
if errorlevel 1 (
    echo Python syntax check failed
    exit /b 1
)
echo Python syntax is valid
goto end

:clean
echo Cleaning up generated files...
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
if exist htmlcov rmdir /s /q htmlcov
if exist .coverage del /q .coverage
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
for /d %%i in (*.egg-info) do if exist "%%i" rmdir /s /q "%%i"
REM Clean Python cache files recursively
for /r . %%i in (*.pyc) do del /q "%%i" 2>nul
for /r . %%i in (__pycache__) do if exist "%%i" rmdir /s /q "%%i" 2>nul
echo Cleanup complete
goto end

:docker_build
echo Building Docker image...
%DOCKER% build -t scraper-app .
if errorlevel 1 (
    echo Docker build failed
    exit /b 1
)
echo Docker image built successfully
goto end

:docker_run
echo Running Docker container...
%DOCKER% run -p 8080:8080 -e BUCKET_NAME=test-bucket scraper-app
goto end

:docker_test
echo Building and testing Docker image...
call :docker_build
if errorlevel 1 exit /b 1
%DOCKER% run --rm -e BUCKET_NAME=test-bucket scraper-app python -c "import main; print('Docker image works')"
goto end

:status
echo.
echo Project Status:
%PYTHON% --version 2>nul || echo Python not found
%PIP% --version 2>nul || echo Pip not found
echo Working directory: %CD%
echo.
%PIP% list 2>nul | findstr /i "flask pytest requests google-cloud" >nul
if errorlevel 1 (
    echo Dependencies: Not all required packages installed
) else (
    echo Dependencies: Required packages appear to be installed
)
echo.
echo Available commands: Run 'make.bat help' for detailed usage
goto end

:end
endlocal 