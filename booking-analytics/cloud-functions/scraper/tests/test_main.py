"""
Comprehensive test suite for the web scraper application.

This file contains unit tests for all major components:
- GCS configuration loading
- Data upload functionality  
- HTTP scraping with retries
- Flask API endpoints
- Integration testing

Each test serves a specific purpose in ensuring production reliability.
"""

import os
import pytest
import json
import requests
import responses
from unittest.mock import Mock, patch, MagicMock

# Mock environment variables before importing main module
with patch.dict('os.environ', {'BUCKET_NAME': 'test-bucket-for-testing'}):
    from main import (
        load_sources_from_gcs, 
        upload_result_to_gcs, 
        fetch_html_with_retries,
        app
    )


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Mock the required environment variable for tests
        with patch.dict('os.environ', {'BUCKET_NAME': 'test-bucket-for-testing'}):
            yield client


class TestLoadSourcesFromGCS:
    """
    Tests for loading scraper configuration from Google Cloud Storage.
    
    These tests ensure the app can reliably read its configuration,
    which is critical for knowing what websites to scrape.
    """

    @patch('main.storage.Client')
    def test_load_sources_success(self, mock_storage_client, sample_sources):
        """
        Test successful loading of sources from GCS.
        
        Purpose: Ensures the core configuration loading mechanism works.
        Real Value: If this fails, the scraper won't know what to scrape.
        Production Impact: Service starts but does nothing without config.
        """
        # Setup mocks to simulate successful GCS interaction
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        # Configure the mock chain: Client -> bucket -> blob
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = json.dumps(sample_sources)
        
        # Execute the function under test
        result = load_sources_from_gcs("test-bucket-for-testing")
        
        # Verify the result matches expected data
        assert result == sample_sources
        
        # Verify all GCS operations were called correctly
        mock_client.bucket.assert_called_once_with("test-bucket-for-testing")
        mock_bucket.blob.assert_called_once_with("config/sources.json")
        mock_blob.exists.assert_called_once()
        mock_blob.download_as_text.assert_called_once()

    @patch('main.storage.Client')
    def test_load_sources_file_not_found(self, mock_storage_client):
        """
        Test behavior when config file doesn't exist in GCS.
        
        Purpose: Ensures graceful handling of missing configuration.
        Real Value: Prevents crashes when config file is accidentally deleted.
        Production Impact: Service stays up, returns empty results vs 500 errors.
        """
        # Setup mocks to simulate missing file
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False  # File doesn't exist
        
        # Execute and verify graceful failure
        result = load_sources_from_gcs("test-bucket-for-testing")
        
        # Should return empty list when file doesn't exist
        assert result == []

    @patch('main.storage.Client')
    def test_load_sources_json_error(self, mock_storage_client):
        """
        Test handling of corrupted/invalid JSON in config file.
        
        Purpose: Ensures robustness against malformed configuration data.
        Real Value: Prevents crashes when someone uploads invalid JSON.
        Production Impact: Keeps service operational despite bad config.
        """
        # Setup mocks to simulate corrupted JSON
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = "invalid json {malformed"
        
        # Execute and verify graceful handling of JSON errors
        result = load_sources_from_gcs("test-bucket-for-testing")
        
        # Should return empty list when JSON is invalid
        assert result == []

    @patch('main.storage.Client')
    def test_load_sources_gcs_exception(self, mock_storage_client):
        """
        Test handling of GCS authentication/network errors.
        
        Purpose: Ensures resilience against cloud service issues.
        Real Value: Handles GCS outages, auth problems, network issues.
        Production Impact: Service degrades gracefully vs crashing.
        """
        # Setup mock to throw exception (simulating GCS error)
        mock_storage_client.side_effect = Exception("GCS connection failed")
        
        # Execute and verify exception handling
        result = load_sources_from_gcs("test-bucket-for-testing")
        
        # Should return empty list when GCS is unavailable
        assert result == []


class TestUploadResultToGCS:
    """
    Tests for uploading scraping results to Google Cloud Storage.
    
    These tests verify that scraped data is properly saved,
    which is the core business value of the scraper.
    """

    @patch('main.storage.Client')
    @patch('main.datetime')
    def test_upload_success(self, mock_datetime, mock_storage_client):
        """
        Test successful upload of scraping results to GCS.
        
        Purpose: Verifies scraped data gets saved correctly.
        Real Value: This IS the core business logic - save scraped data.
        Production Impact: Without this, scraping is pointless (no data saved).
        """
        # Setup time mock for consistent timestamps
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
        
        # Setup GCS mocks
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Test data to upload
        test_data = {
            "source": "test-site",
            "url": "https://test.com", 
            "status": "success",
            "html": "<html>Test</html>"
        }
        
        # Execute upload
        upload_result_to_gcs("test-source", test_data)
        
        # Verify all GCS operations were called correctly
        mock_client.bucket.assert_called_once_with('test-bucket-for-testing')
        mock_bucket.blob.assert_called_once_with("data/test-source/2024-01-01T00:00:00.json")
        mock_blob.upload_from_string.assert_called_once_with(
            json.dumps(test_data), 
            content_type="application/json"
        )

    @patch('main.storage.Client')
    @patch('main.datetime')
    def test_upload_gcs_exception(self, mock_datetime, mock_storage_client):
        """
        Test handling of GCS upload failures.
        
        Purpose: Ensures upload errors don't crash the service.
        Real Value: Shows resilience when GCS has issues.
        Production Impact: Scraping continues even if some uploads fail.
        """
        # Setup time mock
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
        
        # Setup GCS mock to fail
        mock_storage_client.side_effect = Exception("GCS upload failed")
        
        # Execute upload (should not raise exception)
        test_data = {"source": "test", "status": "success"}
        
        # Should handle exception gracefully
        try:
            upload_result_to_gcs("test-source", test_data)
        except Exception:
            pytest.fail("upload_result_to_gcs should handle exceptions gracefully")


class TestFetchHTMLWithRetries:
    """
    Tests for HTTP scraping functionality with retry logic.
    
    These tests verify the core scraping mechanism handles
    real-world issues like network timeouts and server errors.
    """

    @responses.activate
    def test_fetch_success(self, sample_html_response):
        """
        Test successful HTML fetching from a website.
        
        Purpose: Tests the happy path for web scraping.
        Real Value: Core business logic - if this fails, no scraping works.
        Production Impact: Without this, the entire service is useless.
        """
        # Setup successful HTTP response
        responses.add(
            responses.GET, 
            "https://example.com", 
            body=sample_html_response, 
            status=200
        )
        
        # Execute scraping
        result = fetch_html_with_retries("https://example.com")
        
        # Verify successful result structure
        assert result["status"] == "success"
        assert result["html"] == sample_html_response
        assert result["http_status"] == 200
        assert result["error_message"] is None

    @responses.activate
    def test_fetch_http_error(self):
        """
        Test handling of HTTP error responses (4xx, 5xx).
        
        Purpose: Tests error handling for server/client errors.
        Real Value: Shows graceful handling when websites return errors.
        Production Impact: Service continues working when some sites are down.
        """
        # Setup HTTP error response
        responses.add(
            responses.GET, 
            "https://example.com", 
            status=404
        )
        
        # Execute scraping
        result = fetch_html_with_retries("https://example.com")
        
        # Verify error is handled gracefully
        assert result["status"] == "error"
        assert result["html"] is None
        assert result["http_status"] == 404
        assert "404" in result["error_message"]

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_with_retries(self, mock_sleep, mock_get):
        """
        Test retry logic for transient network failures.
        
        Purpose: Tests retry mechanism for temporary failures.
        Real Value: CRITICAL - handles real-world network issues.
        Production Impact: Much higher success rate vs single-attempt scraping.
        """
        # Setup sequence: fail twice, then succeed
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            requests.exceptions.ConnectionError("Network error"),
            Mock(status_code=200, text="<html>Success</html>")
        ]
        
        # Execute with retries
        result = fetch_html_with_retries("https://example.com", max_retries=3)
        
        # Verify eventual success after retries
        assert result["status"] == "success"
        assert result["html"] == "<html>Success</html>"
        assert result["http_status"] == 200
        
        # Verify retry behavior
        assert mock_get.call_count == 3  # 2 failures + 1 success
        assert mock_sleep.call_count == 2  # Sleep between attempts

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_max_retries_exceeded(self, mock_sleep, mock_get):
        """
        Test behavior when all retry attempts fail.
        
        Purpose: Tests final failure after exhausting all retries.
        Real Value: Ensures service doesn't hang on permanently broken sites.
        Production Impact: Clean failure handling vs infinite loops.
        """
        # Setup all attempts to fail
        mock_get.side_effect = requests.exceptions.ConnectionError("Persistent error")
        
        # Execute with limited retries
        result = fetch_html_with_retries("https://example.com", max_retries=2)
        
        # Verify final failure
        assert result["status"] == "error"
        assert result["html"] is None
        assert result["http_status"] is None
        assert "after 2 attempts" in result["error_message"]
        
        # Verify retry attempts were made
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1  # Sleep between attempts (not after last)

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_timeout_handling(self, mock_sleep, mock_get):
        """
        Test handling of request timeouts.
        
        Purpose: Tests timeout handling for slow/unresponsive sites.
        Real Value: Prevents hanging on slow websites.
        Production Impact: Service remains responsive vs waiting forever.
        """
        # Setup timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Execute
        result = fetch_html_with_retries("https://example.com", max_retries=1)
        
        # Verify timeout is handled as an error
        assert result["status"] == "error"
        assert "timeout" in result["error_message"].lower()


class TestFlaskRoutes:
    """
    Tests for Flask API endpoints.
    
    These tests verify the web interface works correctly.
    """

    def test_health_check(self, client):
        """
        Test health check endpoint functionality.
        
        Purpose: Tests the health endpoint required by Cloud Run.
        Real Value: ESSENTIAL for Cloud Run - determines if service gets traffic.
        Production Impact: If this fails, Cloud Run marks service unhealthy.
        """
        # Execute health check
        response = client.get('/health')
        
        # Verify health response structure
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert "timestamp" in data
        
        # Verify timestamp format (should be ISO format)
        import datetime
        try:
            datetime.datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Health check timestamp is not in valid ISO format")

    def test_invalid_route(self, client):
        """
        Test handling of invalid API routes.
        
        Purpose: Ensures 404 handling for non-existent endpoints.
        Real Value: Proper HTTP behavior for API clients.
        Production Impact: Clean API behavior for monitoring/clients.
        """
        # Request non-existent endpoint
        response = client.get('/nonexistent')
        
        # Should return 404
        assert response.status_code == 404


class TestIntegration:
    """
    Integration tests that test multiple components together.
    
    These tests are the most valuable as they catch issues that
    unit tests miss when components interact in unexpected ways.
    """

    @patch('main.storage.Client')
    def test_bucket_configuration_and_folder_structure(self, mock_storage_client):
        """
        Test that GCS bucket is configured with correct folder structure.
        
        Purpose: Verifies bucket and folder organization matches requirements.
        Real Value: CRITICAL - ensures data is stored in the right place.
        Production Impact: Wrong paths = lost data and broken workflows.
        """
        # Setup mocks
        mock_client = Mock()
        mock_bucket = Mock()
        mock_config_blob = Mock()
        mock_data_blob = Mock()
        
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        
        # Test config loading from correct path
        mock_bucket.blob.return_value = mock_config_blob
        mock_config_blob.exists.return_value = True
        mock_config_blob.download_as_text.return_value = json.dumps([
            {"name": "test-site", "url": "https://test.com"}
        ])
        
        # Test that sources are loaded from config/ folder
        sources = load_sources_from_gcs("sports-booking-webscraper")
        
        # Verify config path is correct
        mock_client.bucket.assert_called_with("sports-booking-webscraper")
        mock_bucket.blob.assert_called_with("config/sources.json")
        assert len(sources) == 1
        assert sources[0]["name"] == "test-site"
        
        # Reset mocks for data upload test
        mock_bucket.reset_mock()
        mock_bucket.blob.return_value = mock_data_blob
        
        # Test that data is uploaded to data/ folder
        test_data = {
            "source": "test-site",
            "url": "https://test.com", 
            "status": "success",
            "html": "<html>Test</html>"
        }
        
        with patch('main.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
            upload_result_to_gcs("test-site", test_data)
        
        # Verify data is stored in correct folder structure
        mock_bucket.blob.assert_called_with("data/test-site/2024-01-01T00:00:00.json")
        mock_data_blob.upload_from_string.assert_called_once_with(
            json.dumps(test_data),
            content_type="application/json"
        ) 