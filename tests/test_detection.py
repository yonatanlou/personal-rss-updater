"""Tests for content detection edge cases and failures."""

import pytest
from bs4 import BeautifulSoup

from rss_updater.detection.detector import SelectorDetector
from rss_updater.detection.post_extractor import PostExtractor


class TestContentDetectionEdgeCases:
    """Test content detection edge cases that could break the system."""

    def test_empty_html_content(self):
        """Test detection with empty or minimal HTML."""
        detector = SelectorDetector()

        # Empty HTML
        empty_soup = BeautifulSoup("", "html.parser")
        selectors = detector.detect_post_selectors(empty_soup, "https://example.com")
        assert len(selectors) == 0

        # HTML with no content
        minimal_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        selectors = detector.detect_post_selectors(minimal_soup, "https://example.com")
        assert len(selectors) == 0

    def test_malformed_html_handling(self):
        """Test detection with malformed HTML structures."""
        detector = SelectorDetector()

        # Unclosed tags
        malformed_html = """
        <div class="post">
            <h2>Post Title</h2>
            <a href="/post1">Link
        <div class="post">
            <h2>Another Post</h2>
        """
        soup = BeautifulSoup(malformed_html, "html.parser")
        selectors = detector.detect_post_selectors(soup, "https://example.com")

        # Should still find some selectors despite malformed HTML
        assert len(selectors) > 0
        assert any("post" in sel.selector for sel in selectors)

    def test_no_posts_found(self):
        """Test behavior when no blog posts are detected."""
        detector = SelectorDetector()

        # HTML with content but no post-like structures
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <header>Header</header>
                <footer>Footer</footer>
                <div class="sidebar">Sidebar content</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        selectors = detector.detect_post_selectors(soup, "https://example.com")

        # Should return empty or very low confidence selectors
        assert len(selectors) == 0 or all(sel["confidence"] < 0.5 for sel in selectors)

    def test_selector_returns_no_elements(self):
        """Test post extraction when selector finds no elements."""
        extractor = PostExtractor()

        html = "<div class='content'>Some content</div>"
        soup = BeautifulSoup(html, "html.parser")

        # Use selector that doesn't match anything
        posts = extractor.extract_posts(
            soup, ".nonexistent-class", "https://example.com", "Test Blog"
        )
        assert len(posts) == 0

    def test_posts_without_links(self):
        """Test extraction of posts that don't have proper links."""
        extractor = PostExtractor()

        html = """
        <div class="post">
            <h2>Post Title</h2>
            <p>Content without any links</p>
        </div>
        <div class="post">
            <h2>Another Post</h2>
            <span>No link element</span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        posts = extractor.extract_posts(soup, ".post", "https://example.com", "Test Blog")

        # Should handle posts without links gracefully
        # Might create posts with base URL or skip them entirely
        assert isinstance(posts, list)

        # If posts are created, they should have valid structure
        for post in posts:
            assert hasattr(post, "title")
            assert hasattr(post, "url")
            assert hasattr(post, "blog_name")

    def test_posts_with_duplicate_titles(self):
        """Test handling of posts with identical titles."""
        extractor = PostExtractor()

        html = """
        <div class="post">
            <h2>Same Title</h2>
            <a href="/post1">Link 1</a>
        </div>
        <div class="post">
            <h2>Same Title</h2>
            <a href="/post2">Link 2</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        posts = extractor.extract_posts(soup, ".post", "https://example.com", "Test Blog")

        assert len(posts) == 2
        # Should differentiate by URL even if titles are same
        urls = [post.url for post in posts]
        assert len(set(urls)) == 2  # Unique URLs

    def test_extremely_long_content(self):
        """Test handling of posts with extremely long titles or content."""
        extractor = PostExtractor()

        long_title = "A" * 10000  # Very long title
        html = f"""
        <div class="post">
            <h2>{long_title}</h2>
            <a href="/post1">Link</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        posts = extractor.extract_posts(soup, ".post", "https://example.com", "Test Blog")

        assert len(posts) == 1
        # Should handle long content without crashing
        assert len(posts[0].title) <= 10000  # Some reasonable limit

    def test_special_characters_in_content(self):
        """Test handling of special characters and encoding issues."""
        extractor = PostExtractor()

        html = """
        <div class="post">
            <h2>Post with émojis 🚀 and special chars: &amp; &lt; &gt;</h2>
            <a href="/post1">Link</a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        posts = extractor.extract_posts(soup, ".post", "https://example.com", "Test Blog")

        assert len(posts) == 1
        # Should properly decode HTML entities and handle Unicode
        title = posts[0].title
        assert "émojis" in title
        assert "🚀" in title
        assert "&amp;" not in title  # Should be decoded to &


if __name__ == "__main__":
    pytest.main([__file__])
