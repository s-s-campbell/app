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
import responses
from unittest.mock import Mock, patch, MagicMock

# Mock environment variables before importing main module
with patch.dict('os.environ', {'BUCKET_NAME': 'test-bucket'}):
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
        with patch.dict('os.environ', {'BUCKET_NAME': 'test-bucket'}):
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
        result = load_sources_from_gcs("test-bucket")
        
        # Verify the result matches expected data
        assert result == sample_sources
        
        # Verify all GCS operations were called correctly
        mock_client.bucket.assert_called_once_with("test-bucket")
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
        result = load_sources_from_gcs("test-bucket")
        
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
        result = load_sources_from_gcs("test-bucket")
        
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
        result = load_sources_from_gcs("test-bucket")
        
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
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
        
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
        mock_client.bucket.assert_called_once_with('test-bucket')
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
        
        Purpose: Ensures upload errors don't crash the scraper.
        Real Value: One failed upload shouldn't stop other scraping.
        Production Impact: Resilience against intermittent GCS issues.
        """
        # Setup time mock
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
        
        # Setup GCS mock to throw exception
        mock_storage_client.side_effect = Exception("Upload failed")
        
        test_data = {"test": "data"}
        
        # This should not raise an exception (graceful handling)
        try:
            upload_result_to_gcs("test-source", test_data)
        except Exception:
            pytest.fail("Upload function should handle GCS exceptions gracefully")


class TestFetchHTMLWithRetries:
    """
    Tests for HTTP scraping functionality with retry logic.
    
    These tests ensure the scraper can reliably fetch web content
    despite network issues, which is essential for data collection.
    """

    @responses.activate
    def test_fetch_success(self, sample_html_response):
        """
        Test successful HTTP request and HTML retrieval.
        
        Purpose: Verifies basic web scraping functionality works.
        Real Value: Core functionality - without this, no data is collected.
        Production Impact: This is the fundamental scraping capability.
        """
        # Mock successful HTTP response
        responses.add(
            responses.GET,
            "https://example.com",
            body=sample_html_response,
            status=200
        )
        
        # Execute HTTP fetch
        result = fetch_html_with_retries("https://example.com")
        
        # Verify successful result structure
        assert result["status"] == "success"
        assert result["html"] == sample_html_response
        assert result["http_status"] == 200
        assert result["error_message"] is None

    @responses.activate
    def test_fetch_http_error(self):
        """
        Test handling of HTTP error responses (404, 500, etc.).
        
        Purpose: Ensures graceful handling of website errors.
        Real Value: Real websites return errors - this prevents crashes.
        Production Impact: One broken site doesn't break entire scraper.
        """
        # Mock HTTP error response
        responses.add(
            responses.GET,
            "https://example.com",
            status=404
        )
        
        # Execute and verify error handling
        result = fetch_html_with_retries("https://example.com")
        
        assert result["status"] == "error"
        assert result["html"] is None
        assert result["http_status"] == 404
        assert "404" in result["error_message"]

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_with_retries(self, mock_sleep, mock_get):
        """
        Test retry mechanism with exponential backoff.
        
        Purpose: Verifies resilience against temporary network issues.
        Real Value: CRITICAL for reliability - networks are flaky.
        Production Impact: Dramatically improves success rate vs single attempts.
        """
        import requests
        
        # Setup: fail twice, succeed on third attempt
        side_effects = [
            requests.exceptions.ConnectionError("Connection error"),  # First attempt fails
            requests.exceptions.ConnectionError("Connection error"),  # Second attempt fails
            Mock(text="<html>Success</html>", status_code=200)  # Third succeeds
        ]
        mock_get.side_effect = side_effects
        
        # Mock the successful response's raise_for_status method
        side_effects[2].raise_for_status = Mock()
        
        # Execute with retries
        result = fetch_html_with_retries("https://example.com", max_retries=3)
        
        # Verify eventual success after retries
        assert result["status"] == "success"
        assert result["html"] == "<html>Success</html>"
        assert mock_get.call_count == 3  # Should have tried 3 times
        assert mock_sleep.call_count == 2  # Should sleep after first two failures

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_max_retries_exceeded(self, mock_sleep, mock_get):
        """
        Test behavior when max retries are exceeded.
        
        Purpose: Ensures scraper doesn't hang on persistently broken sites.
        Real Value: Prevents resource exhaustion and timeouts.
        Production Impact: One dead site doesn't block other scraping.
        """
        import requests
        
        # Setup persistent failure
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        # Execute with limited retries
        result = fetch_html_with_retries("https://example.com", max_retries=2)
        
        # Verify graceful failure after exhausting retries
        assert result["status"] == "error"
        assert result["html"] is None
        assert result["http_status"] is None
        assert "Request failed after 2 attempts" in result["error_message"]
        assert mock_get.call_count == 2  # Should stop after max retries

    @patch('main.requests.get')
    @patch('main.time.sleep')
    def test_fetch_timeout_handling(self, mock_sleep, mock_get):
        """
        Test handling of request timeouts.
        
        Purpose: Ensures timeouts are handled properly.
        Real Value: Prevents hanging on slow/unresponsive sites.
        Production Impact: Keeps scraper responsive and efficient.
        """
        # Setup timeout exception
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        # Execute and verify timeout handling
        result = fetch_html_with_retries("https://example.com", max_retries=1)
        
        assert result["status"] == "error"
        assert "Request failed after 1 attempts" in result["error_message"]


class TestFlaskRoutes:
    """
    Tests for Flask API endpoints.
    
    These tests verify the web API behaves correctly for clients,
    which is essential for Cloud Run deployment and monitoring.
    """

    @patch('main.load_sources_from_gcs')
    @patch('main.fetch_html_with_retries')
    @patch('main.upload_result_to_gcs')
    def test_scrape_sites_success(self, mock_upload, mock_fetch, mock_load, client, sample_sources):
        """
        Test successful end-to-end scraping via API endpoint.
        
        Purpose: Tests the complete happy-path workflow.
        Real Value: This is an END-TO-END test of main business process.
        Production Impact: Verifies entire scraping pipeline works together.
        """
        # Setup mocks for successful scraping
        mock_load.return_value = sample_sources
        mock_fetch.return_value = {
            "status": "success",
            "html": "<html>Test</html>",
            "http_status": 200,
            "error_message": None
        }
        
        # Execute API request
        response = client.get('/')
        
        # Verify API response structure and data
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "results" in data
        assert len(data["results"]) == 3  # Should match sample_sources length
        assert data["results"][0]["example"] == "success"
        assert data["results"][1]["test-site"] == "success"
        assert data["results"][2]["booking-site"] == "success"
        
        # Verify all components were called
        mock_load.assert_called_once()
        assert mock_fetch.call_count == 3  # One call per source
        assert mock_upload.call_count == 3  # One upload per source

    @patch('main.load_sources_from_gcs')
    def test_scrape_sites_no_sources(self, mock_load, client):
        """
        Test scraping endpoint behavior with empty configuration.
        
        Purpose: Tests behavior with no work to do.
        Real Value: Ensures valid response during system maintenance/config updates.
        Production Impact: Prevents errors when config is temporarily empty.
        """
        # Setup empty sources
        mock_load.return_value = []
        
        # Execute API request
        response = client.get('/')
        
        # Verify graceful handling of empty config
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["results"] == []

    @patch('main.load_sources_from_gcs')
    @patch('main.fetch_html_with_retries')
    @patch('main.upload_result_to_gcs')
    def test_scrape_sites_mixed_results(self, mock_upload, mock_fetch, mock_load, client, sample_sources):
        """
        Test scraping with mixed success/failure results.
        
        Purpose: Tests realistic scenario where some sites succeed, others fail.
        Real Value: Ensures partial failures don't break the entire response.
        Production Impact: Service remains useful even when some sites are down.
        """
        # Setup mixed results
        mock_load.return_value = sample_sources[:2]  # Only first two sources
        
        # Mock different results for different sites
        mock_fetch.side_effect = [
            {  # First site succeeds
                "status": "success",
                "html": "<html>Success</html>",
                "http_status": 200,
                "error_message": None
            },
            {  # Second site fails
                "status": "error",
                "html": None,
                "http_status": 404,
                "error_message": "404 Not Found"
            }
        ]
        
        # Execute API request
        response = client.get('/')
        
        # Verify mixed results are handled correctly
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["results"]) == 2
        assert data["results"][0]["example"] == "success"
        assert data["results"][1]["test-site"] == "error"

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
    @responses.activate
    def test_end_to_end_scraping(self, mock_storage_client, client, sample_sources, sample_html_response):
        """
        Test complete scraping flow with mocked external services.
        
        Purpose: Tests all components working together in realistic scenario.
        Real Value: MOST IMPORTANT TEST - catches integration bugs unit tests miss.
        Production Impact: Simulates real user requests, verifies complete functionality.
        """
        # Setup GCS mocks for configuration loading and result uploading
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = json.dumps(sample_sources)
        
        # Setup HTTP mocks for each source
        for source in sample_sources:
            responses.add(
                responses.GET, 
                source["url"], 
                body=sample_html_response, 
                status=200
            )
        
        # Execute complete workflow
        response = client.get('/')
        
        # Verify end-to-end success
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["results"]) == len(sample_sources)
        
        # Verify each source was processed successfully
        for i, source in enumerate(sample_sources):
            assert data["results"][i][source["name"]] == "success"
        
        # Verify GCS operations occurred for each source
        assert mock_blob.upload_from_string.call_count == len(sample_sources)
        
        # Verify HTTP requests were made to each source
        assert len(responses.calls) == len(sample_sources)

    @patch('main.storage.Client')
    @responses.activate
    def test_end_to_end_with_failures(self, mock_storage_client, client):
        """
        Test end-to-end flow when some operations fail.
        
        Purpose: Verifies graceful degradation when things go wrong.
        Real Value: CRITICAL - shows system resilience in production.
        Production Impact: Partial failures shouldn't break everything.
        """
        # Mock GCS failure
        mock_storage_client.side_effect = Exception("GCS unavailable")
        
        # Mock failed HTTP request
        responses.add(
            responses.GET,
            "https://example.com",
            status=500  # Server error
        )
        
        # Execute request (should not crash despite failures)
        response = client.get('/')
        
        # Verify graceful handling
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data
        # Results should reflect failures, not crash

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
            mock_datetime.datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
            upload_result_to_gcs("test-site", test_data)
        
        # Verify data is stored in correct folder structure
        mock_bucket.blob.assert_called_with("data/test-site/2024-01-01T00:00:00.json")
        mock_data_blob.upload_from_string.assert_called_once_with(
            json.dumps(test_data),
            content_type="application/json"
        ) 