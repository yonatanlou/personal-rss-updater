"""Tests for the scraper module."""

from rss_updater.scraper import WebScraper
from rss_updater.utils import validate_url, normalize_url, clean_text, extract_excerpt


def test_url_validation():
    """Test URL validation function."""
    assert validate_url("https://example.com") == True
    assert validate_url("http://example.com") == True
    assert validate_url("example.com") == False
    assert validate_url("not-a-url") == False
    assert validate_url("") == False


def test_url_normalization():
    """Test URL normalization function."""
    assert normalize_url("example.com") == "https://example.com"
    assert normalize_url("http://example.com") == "http://example.com"
    assert normalize_url("https://example.com#fragment") == "https://example.com"
    assert normalize_url("https://example.com/path?query=1") == "https://example.com/path?query=1"


def test_text_cleaning():
    """Test text cleaning utilities."""
    assert clean_text("  Hello   world  ") == "Hello world"
    assert clean_text("Hello\n\tworld") == "Hello world"
    assert clean_text("&amp; &lt; &gt;") == "& < >"
    assert clean_text("") == ""


def test_excerpt_extraction():
    """Test excerpt extraction."""
    text = "This is a test sentence. This is another sentence. And one more."
    excerpt = extract_excerpt(text, 30)
    assert len(excerpt) <= 35  # Allow for ellipsis
    assert "test sentence" in excerpt


def test_web_scraper_initialization():
    """Test WebScraper initialization."""
    scraper = WebScraper()
    assert scraper.timeout == 30
    assert "Personal RSS Updater" in scraper.session.headers['User-Agent']
    scraper.close()


def test_web_scraper_context_manager():
    """Test WebScraper as context manager."""
    with WebScraper() as scraper:
        assert scraper.session is not None
    # Session should be closed after context exit


if __name__ == "__main__":
    test_url_validation()
    test_url_normalization()
    test_text_cleaning()
    test_excerpt_extraction()
    test_web_scraper_initialization()
    test_web_scraper_context_manager()
    print("All scraper tests passed!")