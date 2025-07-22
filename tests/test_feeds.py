"""Tests for RSS/Atom feed functionality."""

from unittest.mock import Mock, patch
from datetime import datetime

from rss_updater.feeds import FeedDetector, FeedParser, FeedValidator
from rss_updater.feeds.models import Feed, FeedEntry


class TestFeedDetector:
    """Test RSS/Atom feed detection."""

    def test_common_feed_paths(self):
        """Test that common feed paths are correctly defined."""
        detector = FeedDetector()
        assert "/feed" in detector.COMMON_FEED_PATHS
        assert "/rss.xml" in detector.COMMON_FEED_PATHS
        assert "/atom.xml" in detector.COMMON_FEED_PATHS

    def test_feed_mime_types(self):
        """Test that feed MIME types are correctly defined."""
        detector = FeedDetector()
        assert "application/rss+xml" in detector.FEED_MIME_TYPES
        assert "application/atom+xml" in detector.FEED_MIME_TYPES
        assert "application/xml" in detector.FEED_MIME_TYPES

    def test_looks_like_feed_url(self):
        """Test URL pattern matching for feeds."""
        detector = FeedDetector()

        assert detector._looks_like_feed_url("https://example.com/feed")
        assert detector._looks_like_feed_url("https://example.com/rss.xml")
        assert detector._looks_like_feed_url("https://example.com/atom.xml")
        assert detector._looks_like_feed_url("https://example.com/posts.rss")

        assert not detector._looks_like_feed_url("https://example.com/about")
        assert not detector._looks_like_feed_url("https://example.com/contact.html")

    def test_score_feed(self):
        """Test feed scoring algorithm."""
        detector = FeedDetector()

        atom_score = detector._score_feed("https://example.com/atom.xml")
        rss_score = detector._score_feed("https://example.com/rss.xml")
        feed_score = detector._score_feed("https://example.com/feed")

        # Atom feeds should score highest
        assert atom_score > rss_score
        assert feed_score > rss_score

    def test_get_base_url(self):
        """Test base URL extraction."""
        detector = FeedDetector()

        assert detector._get_base_url("https://example.com/blog/post") == "https://example.com"
        assert detector._get_base_url("http://test.org/feed.xml") == "http://test.org"


class TestFeedParser:
    """Test RSS/Atom feed parsing."""

    def test_get_text_content(self):
        """Test HTML content cleaning."""
        parser = FeedParser()

        # Basic HTML stripping
        html_content = "<p>Hello <strong>world</strong>!</p>"
        assert parser._get_text_content(html_content) == "Hello world!"

        # HTML entities
        entity_content = "Hello &amp; goodbye &lt;test&gt;"
        assert parser._get_text_content(entity_content) == "Hello & goodbye <test>"

        # Empty content
        assert parser._get_text_content("") == ""
        assert parser._get_text_content(None) == ""

        # Dict content (like from feedparser)
        dict_content = {"value": "Test content"}
        assert parser._get_text_content(dict_content) == "Test content"

    @patch("rss_updater.feeds.parser.feedparser.parse")
    def test_parse_feed_success(self, mock_parse):
        """Test successful feed parsing."""
        # Create a more realistic mock that behaves like a feedparser result
        from types import SimpleNamespace

        # Mock feed data
        mock_feed_data = {
            "title": "Test Blog",
            "link": "https://example.com",
            "description": "A test blog",
        }

        # Mock entry data
        mock_entry_data = {
            "title": "Test Post",
            "link": "https://example.com/post1",
            "description": "A test post",
            "id": "post1",
            "guid": "post1",
            "published_parsed": (2024, 1, 1, 12, 0, 0, 0, 1, 0),
        }

        # Create mock entry with both dict-style and attribute access
        mock_entry = SimpleNamespace(**mock_entry_data)
        mock_entry.get = lambda key, default=None: mock_entry_data.get(key, default)

        # Create mock feed with both dict-style and attribute access
        mock_feed = SimpleNamespace(**mock_feed_data)
        mock_feed.get = lambda key, default=None: mock_feed_data.get(key, default)

        # Mock parsed result
        mock_parsed = SimpleNamespace()
        mock_parsed.status = 200
        mock_parsed.bozo = False
        mock_parsed.feed = mock_feed
        mock_parsed.entries = [mock_entry]
        mock_parsed.version = "rss20"

        mock_parse.return_value = mock_parsed

        parser = FeedParser()
        feed = parser.parse_feed("https://example.com/feed.xml")

        assert feed is not None
        assert feed.title == "Test Blog"
        assert feed.feed_type == "rss"
        assert len(feed.entries) == 1
        assert feed.entries[0].title == "Test Post"

    @patch("rss_updater.feeds.parser.feedparser.parse")
    def test_parse_feed_http_error(self, mock_parse):
        """Test feed parsing with HTTP error."""
        mock_parsed = Mock()
        mock_parsed.status = 404
        mock_parse.return_value = mock_parsed

        parser = FeedParser()
        feed = parser.parse_feed("https://example.com/nonexistent.xml")

        assert feed is None

    @patch("rss_updater.feeds.parser.feedparser.parse")
    def test_parse_feed_not_modified(self, mock_parse):
        """Test feed parsing with 304 Not Modified response."""
        mock_parsed = Mock()
        mock_parsed.status = 304
        mock_parse.return_value = mock_parsed

        parser = FeedParser()
        feed = parser.parse_feed("https://example.com/feed.xml", etag="test-etag")

        assert feed is None


class TestFeedValidator:
    """Test RSS/Atom feed validation."""

    def test_feed_health_initialization(self):
        """Test FeedHealth object initialization."""
        from rss_updater.feeds.validator import FeedHealth

        health = FeedHealth(url="https://example.com/feed.xml", is_valid=True, is_reachable=True)

        assert health.url == "https://example.com/feed.xml"
        assert health.is_valid is True
        assert health.is_reachable is True
        assert health.errors == []
        assert health.warnings == []

    @patch("rss_updater.feeds.validator.requests.get")
    @patch("rss_updater.feeds.validator.FeedParser.parse_feed")
    def test_validate_feed_success(self, mock_parse_feed, mock_get):
        """Test successful feed validation."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/feed.xml"
        mock_response.headers = {
            "content-type": "application/rss+xml",
            "etag": "test-etag",
            "last-modified": "Mon, 01 Jan 2024 12:00:00 GMT",
        }
        mock_get.return_value = mock_response

        # Mock feed parsing
        mock_feed = Mock()
        mock_feed.entries = [Mock(), Mock()]  # 2 entries
        mock_feed.feed_type = "rss"
        mock_parse_feed.return_value = mock_feed

        validator = FeedValidator()
        health = validator.validate_feed("https://example.com/feed.xml")

        assert health.is_valid is True
        assert health.is_reachable is True
        assert health.status_code == 200
        assert health.entry_count == 2
        assert health.feed_type == "rss"
        assert health.etag == "test-etag"

    @patch("rss_updater.feeds.validator.requests.get")
    def test_validate_feed_connection_error(self, mock_get):
        """Test feed validation with connection error."""
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection failed")

        validator = FeedValidator()
        health = validator.validate_feed("https://nonexistent.com/feed.xml")

        assert health.is_valid is False
        assert health.is_reachable is False
        assert len(health.errors) > 0
        assert "Connection error" in health.errors[0]

    def test_generate_health_report(self):
        """Test health report generation."""
        from rss_updater.feeds.validator import FeedHealth

        validator = FeedValidator()

        # Create sample health results
        health_results = {
            "https://good.com/feed.xml": FeedHealth(
                url="https://good.com/feed.xml", is_valid=True, is_reachable=True, entry_count=10
            ),
            "https://warning.com/feed.xml": FeedHealth(
                url="https://warning.com/feed.xml",
                is_valid=True,
                is_reachable=True,
                warnings=["Feed has no entries"],
            ),
            "https://broken.com/feed.xml": FeedHealth(
                url="https://broken.com/feed.xml",
                is_valid=False,
                is_reachable=False,
                errors=["Connection error"],
            ),
        }

        report = validator.generate_health_report(health_results)

        assert "FEED HEALTH REPORT" in report
        assert "Total feeds checked: 3" in report
        assert "Valid feeds: 2/3" in report
        assert "HEALTHY FEEDS" in report
        assert "FEEDS WITH WARNINGS" in report
        assert "BROKEN FEEDS" in report


class TestFeedModels:
    """Test feed data models."""

    def test_feed_entry_creation(self):
        """Test FeedEntry model creation and validation."""
        entry = FeedEntry(
            title="Test Post",
            link="https://example.com/post",
            description="A test post",
            published=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert entry.title == "Test Post"
        assert str(entry.link) == "https://example.com/post"
        assert entry.description == "A test post"
        assert entry.published.year == 2024

    def test_feed_creation(self):
        """Test Feed model creation and validation."""
        entries = [
            FeedEntry(title="Post 1", link="https://example.com/post1"),
            FeedEntry(title="Post 2", link="https://example.com/post2"),
        ]

        feed = Feed(
            title="Test Blog",
            link="https://example.com",
            description="A test blog",
            entries=entries,
            feed_type="rss",
        )

        assert feed.title == "Test Blog"
        assert str(feed.link) == "https://example.com/"
        assert len(feed.entries) == 2
        assert feed.feed_type == "rss"

        # Test string representation
        str_repr = str(feed)
        assert "Test Blog" in str_repr
        assert "2 entries" in str_repr
