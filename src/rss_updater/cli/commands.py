"""Command handlers for the RSS updater CLI."""

import sys
from pathlib import Path

from ..core import load_config
from ..storage import BlogStorage
from ..initializer import initialize_blog_states
from ..monitoring import (
    analyze_failed_blogs,
    analyze_blog_structure,
    test_manual_selector,
    BlogMonitor,
)
from ..feeds import FeedDetector, FeedValidator, HybridBlogMonitor
from ..notification import EmailNotifier


class CommandHandler:
    """Handles execution of different CLI commands."""

    def __init__(self, args):
        """Initialize command handler with parsed arguments."""
        self.args = args

    def handle_init(self) -> None:
        """Handle blog initialization command."""
        print("\n=== INITIALIZATION MODE ===")
        try:
            initialize_blog_states(mark_as_read=self.args.mark_as_read)
            print("Blog initialization completed successfully!")
        except Exception as e:
            print(f"Initialization failed: {e}")
            sys.exit(1)

    def handle_sync(self) -> None:
        """Handle blog sync command."""
        print("\n=== SYNC MODE ===")
        try:
            # Load config and storage
            load_config()  # Load config for initialization
            storage = BlogStorage()

            print("Syncing blog states with blogs.json configuration...")

            # Load blogs from config
            blogs_file = Path("config/app/blogs.json")
            if not blogs_file.exists():
                blogs_file = Path("blogs.json")  # Fallback to old location

            if blogs_file.exists():
                import json

                with open(blogs_file, "r") as f:
                    blogs = json.load(f)

                # Sync with storage
                storage.sync_with_blogs(blogs)
                storage.save()

                print(f"Successfully synced {len(blogs)} blogs")
            else:
                print("No blogs.json file found")
                sys.exit(1)
        except Exception as e:
            print(f"Sync failed: {e}")
            sys.exit(1)

    def handle_analyze(self) -> None:
        """Handle blog analysis command."""
        print("\n=== ANALYSIS MODE ===")
        try:
            if self.args.url and self.args.blog_name:
                analyze_blog_structure(self.args.url, self.args.blog_name)
            else:
                analyze_failed_blogs()
        except Exception as e:
            print(f"Analysis failed: {e}")
            sys.exit(1)

    def handle_test_selector(self) -> None:
        """Handle manual selector testing."""
        if not self.args.url or not self.args.selector:
            print("Error: --url and --selector are required for test-selector command")
            sys.exit(1)

        print(f"\n=== TESTING SELECTOR: {self.args.selector} ===")
        try:
            test_manual_selector(self.args.url, self.args.selector)
        except Exception as e:
            print(f"Selector test failed: {e}")
            sys.exit(1)

    def handle_check(self) -> None:
        """Handle blog checking without email."""
        print("\n=== CHECK MODE (No email) ===")
        try:
            # Load configuration
            config = load_config()
            # Initialize monitoring
            monitor = BlogMonitor(config)

            # Check all blogs
            results = monitor.check_all_blogs()
            new_posts = results.get("new_posts", [])

            if new_posts:
                print(f"\nFound {len(new_posts)} new posts:")
                for post in new_posts:
                    print(f"- {post.blog_name}: {post.title}")
                    print(f"  URL: {post.url}")
            else:
                print("No new posts found.")

            # Show summary
            print("\n=== SUMMARY ===")
            summary = monitor.get_summary()
            for line in summary:
                print(line)
        except Exception as e:
            print(f"Check failed: {e}")
            sys.exit(1)

    def handle_test_email(self) -> None:
        """Handle email testing command."""
        print("\n=== EMAIL TEST MODE ===")
        try:
            config = load_config()
            if not config.email.username or not config.email.password:
                print("ERROR: Email credentials not configured!")
                print("Set EMAIL_USERNAME and EMAIL_PASSWORD environment variables")
                sys.exit(1)

            notifier = EmailNotifier(config)

            # Send test email
            success = notifier.send_test_email()

            if success:
                print("✅ Test email sent successfully!")
                print(f"Check your inbox at: {config.email.recipient}")
            else:
                print("❌ Failed to send test email")
                print("Check your email configuration and credentials")
                sys.exit(1)
        except Exception as e:
            print(f"Email test failed: {e}")
            sys.exit(1)

    def handle_detect_feeds(self) -> None:
        """Handle RSS feed detection command."""
        if not self.args.url:
            print("Error: --url is required for detect-feeds command")
            sys.exit(1)

        print(f"\n=== DETECTING FEEDS FOR: {self.args.url} ===")
        try:
            detector = FeedDetector()
            feeds = detector.detect_feeds(self.args.url)

            if feeds:
                print(f"Found {len(feeds)} potential feeds:")
                for i, feed_url in enumerate(feeds, 1):
                    print(f"{i}. {feed_url}")
            else:
                print("No RSS feeds found.")
        except Exception as e:
            print(f"Feed detection failed: {e}")
            sys.exit(1)

    def handle_validate_feed(self) -> None:
        """Handle RSS feed validation command."""
        if not self.args.url:
            print("Error: --url is required for validate-feed command")
            sys.exit(1)

        print(f"\n=== VALIDATING FEED: {self.args.url} ===")
        try:
            validator = FeedValidator()
            health = validator.validate_feed(self.args.url)

            print(f"Feed URL: {health.url}")
            print(f"Valid: {'✅' if health.is_valid else '❌'}")
            print(f"Reachable: {'✅' if health.is_reachable else '❌'}")

            if health.status_code:
                print(f"Status Code: {health.status_code}")
            if health.response_time:
                print(f"Response Time: {health.response_time:.2f}s")
            if health.entry_count:
                print(f"Entries: {health.entry_count}")
            if health.feed_type:
                print(f"Type: {health.feed_type}")
            if health.last_updated:
                print(f"Last Updated: {health.last_updated}")

            if health.warnings:
                print("\n⚠️  Warnings:")
                for warning in health.warnings:
                    print(f"  - {warning}")

            if health.errors:
                print("\n❌ Errors:")
                for error in health.errors:
                    print(f"  - {error}")
        except Exception as e:
            print(f"Feed validation failed: {e}")
            sys.exit(1)

    def handle_hybrid_check(self) -> None:
        """Handle hybrid monitoring (RSS + scraping fallback)."""
        print("\n=== HYBRID CHECK MODE ===")
        try:
            config = load_config()
            monitor = HybridBlogMonitor(config)

            # Run hybrid monitoring
            results = monitor.check_all_blogs()
            new_posts = results.get("new_posts", [])

            if new_posts:
                print(f"\nFound {len(new_posts)} new posts:")
                for post in new_posts:
                    print(f"- {post.blog_name}: {post.title}")
                    print(f"  URL: {post.url}")
            else:
                print("No new posts found.")

            # Show summary
            print(monitor.get_summary())
        except Exception as e:
            print(f"Hybrid check failed: {e}")
            sys.exit(1)

    def handle_run(self) -> None:
        """Handle main run command."""
        print("\n=== MONITORING MODE ===")
        try:
            config = load_config()

            if self.args.use_hybrid:
                # Use hybrid monitoring
                monitor = HybridBlogMonitor(config)
                results = monitor.check_all_blogs()
            else:
                # Use traditional scraping
                monitor = BlogMonitor(config)
                results = monitor.check_all_blogs()

            # Extract results
            new_posts = results.get("new_posts", [])
            stats = results.get("stats", {})
            failed_blogs = results.get("failed_blogs", {})

            # Create failed blogs summary with clickable links
            failed_blogs_summary = ""
            if failed_blogs:
                blog_links = []
                for blog_name, blog_state in failed_blogs.items():
                    blog_links.append(f"{blog_name}: {blog_state.url}")
                failed_blogs_summary = f"Failed blogs:\n{chr(10).join(blog_links)}"

            # Send email if new posts found or there are failures
            if new_posts or failed_blogs:
                if new_posts:
                    print(f"Found {len(new_posts)} new posts, sending email notification...")
                if failed_blogs:
                    print(f"Found {len(failed_blogs)} failed blogs, including in notification...")

                notifier = EmailNotifier(config)
                success = notifier.send_digest(new_posts, stats, failed_blogs_summary)

                if success:
                    print("✅ Email digest sent successfully!")
                    # Only mark posts as notified after successful email
                    if new_posts:
                        monitor.mark_posts_as_notified(new_posts)
                        print(f"✅ Marked {len(new_posts)} posts as notified in storage")
                else:
                    print("❌ Failed to send email digest")
                    print("⚠️  Posts remain unmarked in storage for retry on next run")
                    sys.exit(1)
            else:
                print("No new posts found. No email sent.")

            # Show summary
            if hasattr(monitor, "get_summary"):
                print("\n=== SUMMARY ===")
                summary = monitor.get_summary()
                if isinstance(summary, list):
                    for line in summary:
                        print(line)
                else:
                    print(summary)
        except Exception as e:
            print(f"Monitoring failed: {e}")
            sys.exit(1)
