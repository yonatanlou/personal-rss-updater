"""RSS/Atom feed auto-detection functionality."""

import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


class FeedDetector:
    """Detects RSS/Atom feeds from web pages."""

    # Common feed paths to check
    COMMON_FEED_PATHS = [
        "/feed",
        "/feed/",
        "/feed.xml",
        "/feed.rss",
        "/rss",
        "/rss/",
        "/rss.xml",
        "/atom.xml",
        "/atom",
        "/index.xml",
        "/feeds/all.atom.xml",
        "/feeds/all.rss.xml",
        "?feed=rss",
        "?feed=rss2",
        "?feed=atom",
    ]

    # MIME types that indicate RSS/Atom feeds
    FEED_MIME_TYPES = {
        "application/rss+xml",
        "application/atom+xml",
        "application/xml",
        "text/xml",
        "application/rdf+xml",
    }

    def __init__(self, user_agent: str = "Mozilla/5.0 (Personal RSS Updater)", timeout: int = 10):
        """Initialize feed detector."""
        self.user_agent = user_agent
        self.timeout = timeout

    def detect_feeds(self, url: str) -> List[str]:
        """
        Detect all available RSS/Atom feeds for a given URL.

        Args:
            url: The website URL to scan for feeds

        Returns:
            List of detected feed URLs
        """
        feeds = set()

        # First, try to detect feeds from HTML link tags
        html_feeds = self._detect_feeds_from_html(url)
        feeds.update(html_feeds)

        # Then, try common feed endpoints
        common_feeds = self._check_common_feed_paths(url)
        feeds.update(common_feeds)

        # Remove duplicates and validate feeds
        valid_feeds = []
        for feed_url in feeds:
            if self._is_valid_feed(feed_url):
                valid_feeds.append(feed_url)

        return valid_feeds

    def _detect_feeds_from_html(self, url: str) -> List[str]:
        """Extract feed URLs from HTML link tags."""
        feeds = []

        try:
            response = requests.get(
                url, headers={"User-Agent": self.user_agent}, timeout=self.timeout
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "lxml")

            # Look for RSS/Atom feed links in HTML head
            feed_links = soup.find_all("link", rel=re.compile(r"alternate", re.I))

            for link in feed_links:
                link_type = link.get("type", "").lower()
                href = link.get("href")

                if href and any(
                    feed_type in link_type for feed_type in ["rss", "atom", "xml", "feed"]
                ):
                    feed_url = urljoin(url, href)
                    feeds.append(feed_url)

            # Also look for feed links in the page content
            feed_links_in_content = soup.find_all("a", href=re.compile(r"feed|rss|atom", re.I))
            for link in feed_links_in_content:
                href = link.get("href")
                if href:
                    feed_url = urljoin(url, href)
                    if self._looks_like_feed_url(feed_url):
                        feeds.append(feed_url)

        except Exception as e:
            print(f"Error detecting feeds from HTML for {url}: {e}")

        return feeds

    def _check_common_feed_paths(self, url: str) -> List[str]:
        """Check common feed paths for the given URL."""
        feeds = []
        base_url = self._get_base_url(url)

        for path in self.COMMON_FEED_PATHS:
            feed_url = urljoin(base_url, path)

            # Quick HEAD request to check if feed exists
            try:
                response = requests.head(
                    feed_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "").lower()
                    if any(mime_type in content_type for mime_type in self.FEED_MIME_TYPES):
                        feeds.append(feed_url)

            except Exception:
                # Ignore failures for common path checks
                continue

        return feeds

    def _is_valid_feed(self, url: str) -> bool:
        """Validate if URL points to a valid RSS/Atom feed."""
        try:
            response = requests.get(
                url, headers={"User-Agent": self.user_agent}, timeout=self.timeout
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if any(mime_type in content_type for mime_type in self.FEED_MIME_TYPES):
                return True

            # Check content for feed indicators
            content = response.text.lower()
            feed_indicators = [
                "<rss",
                "<feed",
                "<rdf:rdf",
                "xmlns:atom",
                'xmlns="http://www.w3.org/2005/atom"',
            ]

            return any(indicator in content for indicator in feed_indicators)

        except Exception:
            return False

    def _looks_like_feed_url(self, url: str) -> bool:
        """Check if URL looks like a feed URL based on pattern matching."""
        url_lower = url.lower()
        feed_patterns = [r"feed", r"rss", r"atom", r"\.xml$", r"\.rss$"]

        return any(re.search(pattern, url_lower) for pattern in feed_patterns)

    def _get_base_url(self, url: str) -> str:
        """Extract base URL from a full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_best_feed(self, url: str) -> Optional[str]:
        """
        Get the best RSS/Atom feed for a given URL.

        Prioritizes feeds in this order:
        1. Atom feeds (more structured)
        2. RSS 2.0 feeds
        3. RSS 1.0 feeds
        4. Any other XML feeds

        Args:
            url: The website URL

        Returns:
            Best feed URL or None if no feeds found
        """
        feeds = self.detect_feeds(url)

        if not feeds:
            return None

        # Score feeds by preference
        scored_feeds = []
        for feed_url in feeds:
            score = self._score_feed(feed_url)
            scored_feeds.append((score, feed_url))

        # Return highest scored feed
        scored_feeds.sort(reverse=True)
        return scored_feeds[0][1] if scored_feeds else None

    def _score_feed(self, feed_url: str) -> int:
        """Score a feed URL based on preferences."""
        score = 0
        url_lower = feed_url.lower()

        # Prefer Atom feeds
        if "atom" in url_lower:
            score += 10

        # Prefer explicit feed paths
        if "/feed" in url_lower:
            score += 5

        # RSS feeds
        if "rss" in url_lower:
            score += 3

        # XML feeds
        if ".xml" in url_lower:
            score += 1

        return score
