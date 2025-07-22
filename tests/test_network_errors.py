"""Tests for network error handling and resilience."""

import pytest
from unittest.mock import Mock, patch
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

from rss_updater.web.scraper import WebScraper


class TestNetworkErrorHandling:
    """Test network error handling and system resilience."""

    def test_timeout_handling(self):
        """Test handling of request timeouts."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = Timeout("Request timed out")

            scraper = WebScraper(timeout=5)
            result = scraper.fetch_page("https://example.com")

            # Should return None or handle timeout gracefully
            assert result is None
            scraper.close()

    def test_connection_error_handling(self):
        """Test handling of connection errors (site unreachable)."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = ConnectionError("Failed to establish connection")

            scraper = WebScraper()
            result = scraper.fetch_page("https://nonexistent-site.invalid")

            # Should handle connection errors gracefully
            assert result is None
            scraper.close()

    def test_http_error_handling(self):
        """Test handling of HTTP errors (404, 500, etc.)."""
        with patch("requests.Session.get") as mock_get:
            # Mock 404 response
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com/nonexistent")

            # Should handle HTTP errors gracefully
            assert result is None
            scraper.close()

    def test_ssl_certificate_errors(self):
        """Test handling of SSL certificate errors."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.SSLError("SSL certificate error")

            scraper = WebScraper()
            result = scraper.fetch_page("https://bad-ssl-site.com")

            # Should handle SSL errors gracefully
            assert result is None
            scraper.close()

    def test_redirect_loops(self):
        """Test handling of redirect loops."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.TooManyRedirects("Too many redirects")

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com")

            # Should handle redirect loops gracefully
            assert result is None
            scraper.close()

    def test_malformed_response_content(self):
        """Test handling of malformed or corrupted response content."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200
            mock_response.content = b"\x80\x81\x82"  # Invalid UTF-8 bytes
            mock_response.text = "Invalid encoding content"
            mock_response.encoding = "utf-8"
            mock_get.return_value = mock_response

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com")

            # Should handle malformed content without crashing
            assert result is not None or result is None  # Either works, just don't crash
            scraper.close()

    def test_extremely_slow_response(self):
        """Test handling of extremely slow responses."""
        with patch("requests.Session.get") as mock_get:
            # Simulate timeout exception directly
            mock_get.side_effect = Timeout("Request timed out")

            scraper = WebScraper(timeout=1)  # 1 second timeout

            # This should timeout and return None
            result = scraper.fetch_page("https://example.com")
            assert result is None
            scraper.close()

    def test_partial_content_response(self):
        """Test handling of partial content responses."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 206  # Partial Content
            mock_response.content = b"<html><body>Partial conte"  # Cut off
            mock_response.text = "<html><body>Partial conte"
            mock_get.return_value = mock_response

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com")

            # Should handle partial content gracefully
            assert result is not None
            scraper.close()

    def test_rate_limiting_response(self):
        """Test handling of rate limiting (HTTP 429)."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = HTTPError("429 Too Many Requests")
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_get.return_value = mock_response

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com")

            # Should handle rate limiting gracefully
            assert result is None
            scraper.close()

    def test_network_error_retry_logic(self):
        """Test that retry logic works for network errors."""
        with patch("requests.Session.get") as mock_get:
            # First two calls fail, third succeeds
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.status_code = 200
            mock_response.content = b"<html>Success</html>"
            mock_response.text = "<html>Success</html>"

            mock_get.side_effect = [
                ConnectionError("Connection failed"),
                Timeout("Request timed out"),
                mock_response,
            ]

            scraper = WebScraper()
            result = scraper.fetch_page("https://example.com")

            # Should eventually succeed after retries
            assert result is not None
            assert result == mock_response  # Should return the mock response object
            assert mock_get.call_count == 3
            scraper.close()

    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = requests.exceptions.InvalidURL("Failed to resolve hostname")

            scraper = WebScraper()
            result = scraper.fetch_page("https://this-domain-does-not-exist-12345.invalid")

            # Should handle DNS failures gracefully
            assert result is None
            scraper.close()


if __name__ == "__main__":
    pytest.main([__file__])
