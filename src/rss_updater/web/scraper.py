"""Web scraping functionality for the RSS updater application."""

import time
from functools import wraps
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def rate_limit(delay: float = 1.0):
    """Decorator to add rate limiting between requests."""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, "_last_request_time"):
                elapsed = time.time() - self._last_request_time
                if elapsed < delay:
                    time.sleep(delay - elapsed)

            result = func(self, *args, **kwargs)
            self._last_request_time = time.time()
            return result

        return wrapper

    return decorator


class WebScraper:
    """Web scraper with session management and error handling."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Personal RSS Updater)", timeout: int = 30):
        """Initialize scraper with session and retry strategy."""
        self.session = requests.Session()
        self.timeout = timeout
        self._last_request_time = 0

        # Set user agent
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,  # Don't raise HTTPError, let us handle it
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @rate_limit(delay=1.0)
    def fetch_page(self, url: str, retries: int = 3) -> Optional[requests.Response]:
        """
        Fetch a web page with error handling and retry logic.

        Args:
            url: The URL to fetch
            retries: Number of retries for connection/timeout errors

        Returns:
            Response object or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == retries - 1:  # Last attempt
                    if isinstance(e, requests.exceptions.Timeout):
                        print(f"Timeout fetching {url}")
                    else:
                        print(f"Connection error fetching {url}")
                continue  # Try again

            except requests.exceptions.HTTPError as e:
                status_code = (
                    getattr(e.response, "status_code", "unknown") if e.response else "unknown"
                )
                print(f"HTTP error {status_code} fetching {url}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"Request error fetching {url}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error fetching {url}: {e}")
                return None

        return None

    def parse_page(self, response: requests.Response) -> Optional[BeautifulSoup]:
        """
        Parse HTML response into BeautifulSoup object.

        Args:
            response: The HTTP response to parse

        Returns:
            BeautifulSoup object or None if parsing failed
        """
        try:
            # Try to detect encoding from response
            response.encoding = response.apparent_encoding or "utf-8"

            soup = BeautifulSoup(response.content, "lxml")
            return soup

        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return None

    def fetch_and_parse(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page in one operation.

        Args:
            url: The URL to fetch and parse

        Returns:
            BeautifulSoup object or None if failed
        """
        response = self.fetch_page(url)
        if response is None:
            return None

        return self.parse_page(response)

    def get_page_info(self, url: str) -> Dict[str, Any]:
        """
        Get basic information about a web page.

        Args:
            url: The URL to analyze

        Returns:
            Dictionary with page information
        """
        info = {
            "url": url,
            "title": None,
            "status_code": None,
            "content_type": None,
            "page_size": None,
            "error": None,
        }

        try:
            response = self.fetch_page(url)
            if response is None:
                info["error"] = "Failed to fetch page"
                return info

            info["status_code"] = response.status_code
            info["content_type"] = response.headers.get("content-type", "unknown")
            info["page_size"] = len(response.content)

            soup = self.parse_page(response)
            if soup:
                title_tag = soup.find("title")
                if title_tag:
                    info["title"] = title_tag.get_text().strip()

        except Exception as e:
            info["error"] = str(e)

        return info

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
