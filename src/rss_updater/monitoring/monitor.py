"""Blog monitoring system for detecting new posts."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..core import AppConfig, Post
from ..detection import SelectorDetector
from ..web import WebScraper
from ..storage import BlogStorage
from ..utils import clean_text


from ..notification.reminder import send_reminder_for_feed_blogs


class BlogMonitor:
    """Orchestrates checking for changes across all blogs."""

    def __init__(self, config: AppConfig, storage: Optional[BlogStorage] = None):
        """Initialize the blog monitor."""
        self.config = config
        self.storage = storage or BlogStorage()
        self.detector = SelectorDetector()
        self.new_posts: List[Post] = []
        self.stats = {
            "total_blogs": 0,
            "checked_blogs": 0,
            "failed_blogs": 0,
            "new_posts_found": 0,
            "errors": [],
        }

    def check_all_blogs(self) -> Dict:
        """
        Check all configured blogs for new posts.

        Returns:
            Dictionary with monitoring results and statistics
        """
        print("Starting blog monitoring...")

        # Load blogs from JSON file
        blogs = self._load_blogs()
        self.stats["total_blogs"] = len(blogs)

        # Handle feed-based blogs
        send_reminder_for_feed_blogs(self.config, self.storage, blogs)

        # Filter for scrape-based blogs
        scrape_blogs = [b for b in blogs if b.get("monitoring_strategy", "scrape") == "scrape"]

        print(f"Checking {len(scrape_blogs)} blogs for new posts...")

        with WebScraper(user_agent=self.config.user_agent) as scraper:
            for i, blog in enumerate(scrape_blogs, 1):
                blog_name = blog["name"]
                blog_url = blog["url"]

                print(f"[{i}/{len(blogs)}] Checking: {blog_name}")

                try:
                    new_post = self.check_blog(scraper, blog_name, blog_url)
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

                    # Increment failure count
                    self.storage.increment_failure_count(blog_name, blog_url)

        # Save updated states
        self.storage.save()

        # Return results
        results = {
            "new_posts": self.new_posts,
            "stats": self.stats,
            "failed_blogs": self.storage.get_failed_blogs(self.config.failure_threshold),
        }

        print("\nMonitoring complete!")
        print(f"✅ Checked: {self.stats['checked_blogs']}/{self.stats['total_blogs']}")
        print(f"🎉 New posts: {self.stats['new_posts_found']}")
        print(f"❌ Failures: {self.stats['failed_blogs']}")

        return results

    def mark_posts_as_notified(self, new_posts: List[Post]) -> None:
        """
        Mark new posts as successfully notified by updating storage.

        This should only be called after email notification succeeds.

        Args:
            new_posts: List of posts that were successfully emailed
        """
        for post in new_posts:
            self.storage.update_latest_post(post.blog_name, post)

        # Save the updated states to disk
        self.storage.save()

    def check_blog(self, scraper: WebScraper, blog_name: str, blog_url: str) -> Optional[Post]:
        """
        Check a single blog for new posts.

        Args:
            scraper: WebScraper instance
            blog_name: Name of the blog
            blog_url: URL of the blog

        Returns:
            Post object if new post found, None otherwise
        """
        # Get current state
        current_state = self.storage.get_blog_state(blog_name)

        # Fetch and parse the page
        soup = scraper.fetch_and_parse(blog_url)
        if not soup:
            raise Exception("Failed to fetch page")

        # Get latest post using intelligent detection
        latest_post_info = self.detector.get_latest_post(soup, blog_url, blog_name)

        if not latest_post_info:
            raise Exception("Could not detect any posts")

        # Create Post object
        latest_post = Post(
            title=latest_post_info["title"], url=latest_post_info["url"], blog_name=blog_name
        )

        # Check if this is a new post
        is_new_post = self._is_new_post(latest_post, current_state)

        # Only reset failure count on successful check (don't update latest post yet)
        self.storage.reset_failure_count(blog_name)

        return latest_post if is_new_post else None

    def _is_new_post(self, latest_post: Post, current_state) -> bool:
        """
        Determine if the latest post is new compared to stored state.

        Args:
            latest_post: The latest post found
            current_state: Current stored state for the blog

        Returns:
            True if post is new, False otherwise
        """
        if not current_state:
            # No previous state - consider it new
            return True

        # Compare with stored latest post
        stored_title = current_state.last_post_title
        stored_url = current_state.last_post_url

        # If no stored post info, consider current post as new
        if not stored_title and not stored_url:
            return True

        # Skip posts marked as "Fallback" from initialization
        if stored_title and stored_title.startswith("Fallback -"):
            return True

        # Compare title and URL
        title_different = clean_text(latest_post.title) != clean_text(stored_title or "")
        url_different = latest_post.url != stored_url

        # Consider new if either title or URL is different
        return title_different or url_different

    def _load_blogs(self) -> List[Dict[str, str]]:
        """Load blog list from JSON file."""
        blogs_file = Path("config/app/blogs.json")

        if not blogs_file.exists():
            raise FileNotFoundError(f"Blog list file not found: {blogs_file}")

        with open(blogs_file, "r") as f:
            blogs = json.load(f)

        return blogs

    def get_summary(self) -> str:
        """Get a text summary of the monitoring results."""
        summary = []
        summary.append(f"Blog Monitoring Summary ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        summary.append("=" * 50)
        summary.append(f"Total blogs: {self.stats['total_blogs']}")
        summary.append(f"Successfully checked: {self.stats['checked_blogs']}")
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


def run_monitoring(config: AppConfig) -> Dict:
    """
    Convenience function to run blog monitoring.

    Args:
        config: Application configuration

    Returns:
        Monitoring results dictionary
    """
    monitor = BlogMonitor(config)
    return monitor.check_all_blogs()
