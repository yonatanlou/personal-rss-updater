"""Hybrid monitoring system that tries RSS first, then falls back to web scraping."""

from typing import Optional, Dict, List
from datetime import datetime
from ..core import Post, AppConfig
from ..web import WebScraper
from ..detection import SelectorDetector
from ..storage import BlogStorage
from ..utils import clean_text
from .parser import FeedParser
from .detector import FeedDetector
from .validator import FeedValidator


class HybridBlogMonitor:
    """
    Hybrid blog monitor that tries RSS feeds first, then falls back to web scraping.

    This approach prioritizes RSS feeds when available as they are:
    - More reliable and structured
    - Faster to parse
    - Less prone to breaking when websites change layout
    - More respectful of server resources
    """

    def __init__(self, config: AppConfig, storage: Optional[BlogStorage] = None):
        """Initialize hybrid monitor."""
        self.config = config
        self.storage = storage or BlogStorage()

        # Web scraping components (fallback)
        self.web_scraper = None
        self.selector_detector = SelectorDetector()

        # RSS/Feed components (primary)
        self.feed_parser = FeedParser(user_agent=self.config.user_agent, timeout=30)
        self.feed_detector = FeedDetector(user_agent=self.config.user_agent, timeout=10)
        self.feed_validator = FeedValidator(user_agent=self.config.user_agent, timeout=30)

        self.stats = {
            "total_blogs": 0,
            "checked_blogs": 0,
            "failed_blogs": 0,
            "new_posts_found": 0,
            "rss_success": 0,
            "scraper_fallback": 0,
            "errors": [],
        }
        self.new_posts: List[Post] = []

    def check_blog(self, blog_name: str, blog_url: str) -> Optional[Post]:
        """
        Check a single blog using hybrid approach.

        Args:
            blog_name: Name of the blog
            blog_url: URL of the blog

        Returns:
            Post object if new post found, None otherwise
        """
        current_state = self.storage.get_blog_state(blog_name)

        # Try RSS approach first
        try:
            rss_post = self._check_blog_via_rss(blog_name, blog_url, current_state)
            if rss_post:
                self.stats["rss_success"] += 1
                print("  📡 RSS: Found via feed")
                return rss_post
        except Exception as e:
            print(f"  📡 RSS: Failed ({e}), trying web scraping...")

        # Fallback to web scraping
        try:
            if not self.web_scraper:
                self.web_scraper = WebScraper(user_agent=self.config.user_agent)

            scraper_post = self._check_blog_via_scraping(blog_name, blog_url, current_state)
            if scraper_post:
                self.stats["scraper_fallback"] += 1
                print("  🔍 SCRAPER: Found via web scraping")
                return scraper_post
        except Exception as e:
            print(f"  🔍 SCRAPER: Failed ({e})")
            raise e

        return None

    def _check_blog_via_rss(self, blog_name: str, blog_url: str, current_state) -> Optional[Post]:
        """Check blog via RSS/Atom feed."""

        # Check if we have a cached feed URL for this blog
        feed_url = self._get_cached_feed_url(blog_name, blog_url)

        if not feed_url:
            # Auto-detect feeds
            detected_feeds = self.feed_detector.detect_feeds(blog_url)
            if not detected_feeds:
                raise Exception("No RSS/Atom feeds found")

            # Use best feed
            feed_url = self.feed_detector.get_best_feed(blog_url)
            if not feed_url:
                feed_url = detected_feeds[0]

            # Cache the feed URL for future use
            self._cache_feed_url(blog_name, blog_url, feed_url)

        # Parse feed with caching support
        etag = None
        modified = None
        if current_state:
            etag = getattr(current_state, "feed_etag", None)
            modified = getattr(current_state, "feed_modified", None)

        feed = self.feed_parser.parse_feed(feed_url, etag=etag, modified=modified)
        if not feed:
            raise Exception("Failed to parse RSS feed")

        if not feed.entries:
            raise Exception("RSS feed has no entries")

        # Get latest entry
        latest_entry = max(feed.entries, key=lambda e: e.published or datetime.min)

        # Convert to Post object
        latest_post = Post(
            title=latest_entry.title,
            url=str(latest_entry.link),
            blog_name=blog_name,
            content=latest_entry.description or latest_entry.content,
            published_date=latest_entry.published,
        )

        # Check if this is a new post
        is_new = self._is_new_post(latest_post, current_state, method="rss")

        if is_new:
            # Update storage with RSS-specific caching info
            self.storage.update_latest_post(blog_name, latest_post)
            self._update_feed_cache_info(blog_name, feed)
            self.storage.reset_failure_count(blog_name)
            return latest_post

        return None

    def _check_blog_via_scraping(
        self, blog_name: str, blog_url: str, current_state
    ) -> Optional[Post]:
        """Check blog via web scraping (fallback method)."""

        # Fetch and parse the page
        soup = self.web_scraper.fetch_and_parse(blog_url)
        if not soup:
            raise Exception("Failed to fetch page")

        # Get latest post using intelligent detection
        latest_post_info = self.selector_detector.get_latest_post(soup, blog_url, blog_name)
        if not latest_post_info:
            raise Exception("Could not detect any posts")

        # Create Post object
        latest_post = Post(
            title=latest_post_info["title"], url=latest_post_info["url"], blog_name=blog_name
        )

        # Check if this is a new post
        is_new = self._is_new_post(latest_post, current_state, method="scraping")

        if is_new:
            self.storage.update_latest_post(blog_name, latest_post)
            self.storage.reset_failure_count(blog_name)
            return latest_post

        return None

    def _is_new_post(self, latest_post: Post, current_state, method: str) -> bool:
        """Check if post is new compared to stored state."""
        if not current_state:
            return True

        stored_title = current_state.last_post_title
        stored_url = current_state.last_post_url

        if not stored_title and not stored_url:
            return True

        # Skip fallback posts from initialization
        if stored_title and stored_title.startswith("Fallback -"):
            return True

        # For RSS method, also compare by publication date if available
        if method == "rss" and latest_post.published_date and current_state.last_post_date:
            if latest_post.published_date <= current_state.last_post_date:
                return False

        # Compare title and URL
        title_different = clean_text(latest_post.title) != clean_text(stored_title or "")
        url_different = latest_post.url != stored_url

        return title_different or url_different

    def _get_cached_feed_url(self, blog_name: str, blog_url: str) -> Optional[str]:
        """Get cached RSS feed URL for a blog."""
        state = self.storage.get_blog_state(blog_name)
        if state and hasattr(state, "feed_url"):
            return state.feed_url
        return None

    def _cache_feed_url(self, blog_name: str, blog_url: str, feed_url: str):
        """Cache RSS feed URL for a blog."""
        state = self.storage.get_blog_state(blog_name)
        if state:
            # Add feed_url to existing state
            state.feed_url = feed_url
            self.storage.save()

    def _update_feed_cache_info(self, blog_name: str, feed):
        """Update RSS feed caching information."""
        state = self.storage.get_blog_state(blog_name)
        if state:
            state.feed_etag = feed.etag
            state.feed_modified = feed.modified
            self.storage.save()

    def check_all_blogs(self) -> Dict:
        """Check all blogs using hybrid approach."""
        print("Starting hybrid blog monitoring (RSS + Web Scraping)...")

        blogs = self._load_blogs()
        self.stats["total_blogs"] = len(blogs)

        print(f"Checking {len(blogs)} blogs for new posts...")

        for i, blog in enumerate(blogs, 1):
            blog_name = blog["name"]
            blog_url = blog["url"]

            print(f"[{i}/{len(blogs)}] Checking: {blog_name}")

            try:
                new_post = self.check_blog(blog_name, blog_url)
                if new_post:
                    self.new_posts.append(new_post)
                    self.stats["new_posts_found"] += 1
                    print(f"  🎉 NEW POST: {new_post.title[:60]}...")
                else:
                    print("  ✓ No new posts")

                self.stats["checked_blogs"] += 1

            except Exception as e:
                error_msg = f"Error checking {blog_name}: {e}"
                print(f"  ❌ {error_msg}")
                self.stats["errors"].append(error_msg)
                self.stats["failed_blogs"] += 1

                self.storage.increment_failure_count(blog_name, blog_url)

        # Clean up web scraper
        if self.web_scraper:
            self.web_scraper.close()

        # Save updated states
        self.storage.save()

        print("\nMonitoring complete!")
        print(f"✅ Checked: {self.stats['checked_blogs']}/{self.stats['total_blogs']}")
        print(f"📡 RSS Success: {self.stats['rss_success']}")
        print(f"🔍 Scraper Fallback: {self.stats['scraper_fallback']}")
        print(f"🎉 New posts: {self.stats['new_posts_found']}")
        print(f"❌ Failures: {self.stats['failed_blogs']}")

        return {
            "new_posts": self.new_posts,
            "stats": self.stats,
            "failed_blogs": self.storage.get_failed_blogs(self.config.failure_threshold),
        }

    def _load_blogs(self) -> List[Dict[str, str]]:
        """Load blog list from JSON file."""
        import json
        from pathlib import Path

        from ..constants import BLOGS_CONFIG_PATH, LEGACY_BLOGS_PATH
        blogs_file = BLOGS_CONFIG_PATH if BLOGS_CONFIG_PATH.exists() else LEGACY_BLOGS_PATH

        if not blogs_file.exists():
            raise FileNotFoundError(f"Blog list file not found: {blogs_file}")

        with open(blogs_file, "r") as f:
            blogs = json.load(f)

        return blogs

    def get_summary(self) -> str:
        """Get text summary of monitoring results."""
        summary = []
        summary.append(
            f"Hybrid Blog Monitoring Summary ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        )
        summary.append("=" * 60)
        summary.append(f"Total blogs: {self.stats['total_blogs']}")
        summary.append(f"Successfully checked: {self.stats['checked_blogs']}")
        summary.append(f"RSS successful: {self.stats['rss_success']}")
        summary.append(f"Web scraper fallback: {self.stats['scraper_fallback']}")
        summary.append(f"Failed checks: {self.stats['failed_blogs']}")
        summary.append(f"New posts found: {self.stats['new_posts_found']}")

        if self.new_posts:
            summary.append("\nNew Posts:")
            summary.append("-" * 20)
            for post in self.new_posts:
                summary.append(f"• {post.blog_name}: {post.title}")
                summary.append(f"  {post.url}")
                summary.append("")

        if self.stats["errors"]:
            summary.append("\nErrors:")
            summary.append("-" * 20)
            for error in self.stats["errors"]:
                summary.append(f"• {error}")

        return "\n".join(summary)

    def get_failed_blogs_summary(self) -> str:
        """Get summary of persistently failed blogs."""
        failed_blogs = self.storage.get_failed_blogs(self.config.failure_threshold)

        if not failed_blogs:
            return ""

        summary = []
        summary.append(f"\n⚠️  Persistently Failed Blogs ({len(failed_blogs)}):")
        summary.append("=" * 40)

        for blog_name, state in failed_blogs.items():
            days_failed = "Unknown"
            if state.last_success:
                days_failed = (datetime.now() - state.last_success).days

            summary.append(f"• {blog_name}")
            summary.append(f"  Failures: {state.failure_count}")
            summary.append(f"  Last success: {state.last_success or 'Never'}")
            summary.append(f"  Days failed: {days_failed}")
            summary.append("")

        return "\n".join(summary)
