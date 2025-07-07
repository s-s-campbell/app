"""
Shared test fixtures and configuration for pytest.
This file contains reusable test data and setup code.
"""

import pytest
import os
from unittest.mock import patch
from main import app


@pytest.fixture
def client():
    """
    Flask test client fixture.
    
    Creates a test client for making HTTP requests to the Flask app
    without actually starting a server. This is essential for testing
    Flask routes and endpoints.
    
    Returns:
        FlaskClient: Test client for making requests to the app
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_bucket_name():
    """
    Mock bucket name for testing.
    
    Provides a consistent test bucket name to avoid using real
    GCS resources during testing.
    
    Returns:
        str: Test bucket name
    """
    return "test-bucket"


@pytest.fixture
def sample_sources():
    """
    Sample sources data for testing.
    
    Provides realistic test data that mimics the structure of
    sources.json config file. This data represents websites
    that would be scraped in production.
    
    Returns:
        list: List of source dictionaries with name and url
    """
    return [
        {"name": "example", "url": "https://example.com"},
        {"name": "test-site", "url": "https://test.com"},
        {"name": "booking-site", "url": "https://booking-example.com"}
    ]


@pytest.fixture
def sample_html_response():
    """
    Sample HTML response for testing scraping functionality.
    
    Returns:
        str: Mock HTML content that would be returned from a website
    """
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Content</h1>
            <p>This is a test page for scraping.</p>
        </body>
    </html>
    """


@pytest.fixture
def mock_environment():
    """
    Mock environment variables for testing.
    
    Sets up environment variables needed for testing without
    affecting the actual system environment.
    
    Returns:
        dict: Dictionary of environment variables for testing
    """
    return {
        'BUCKET_NAME': 'test-bucket',
        'PORT': '8080'
    } 