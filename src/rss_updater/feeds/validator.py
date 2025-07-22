"""Feed validation and health check functionality."""

import time
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
import requests
from .parser import FeedParser


@dataclass
class FeedHealth:
    """Represents the health status of a feed."""

    url: str
    is_valid: bool
    is_reachable: bool
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    last_updated: Optional[datetime] = None
    entry_count: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    feed_type: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    redirect_url: Optional[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class FeedValidator:
    """Validates RSS/Atom feeds and performs health checks."""

    def __init__(self, timeout: int = 30, user_agent: str = "Mozilla/5.0 (Personal RSS Updater)"):
        """Initialize feed validator."""
        self.timeout = timeout
        self.user_agent = user_agent
        self.parser = FeedParser(user_agent=user_agent, timeout=timeout)

    def validate_feed(self, url: str) -> FeedHealth:
        """
        Perform comprehensive validation of a feed.

        Args:
            url: Feed URL to validate

        Returns:
            FeedHealth object with validation results
        """
        health = FeedHealth(url=url, is_valid=False, is_reachable=False)

        # Test basic connectivity
        start_time = time.time()
        try:
            response = requests.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
                allow_redirects=True,
            )

            health.response_time = time.time() - start_time
            health.status_code = response.status_code
            health.is_reachable = response.status_code == 200

            # Check for redirects
            if response.url != url:
                health.redirect_url = response.url
                health.warnings.append(f"Feed redirected from {url} to {response.url}")

            # Check caching headers
            health.etag = response.headers.get("etag")
            health.last_modified = response.headers.get("last-modified")

            if not health.etag and not health.last_modified:
                health.warnings.append("No caching headers (ETag/Last-Modified) found")

            # Validate content type
            content_type = response.headers.get("content-type", "").lower()
            valid_types = [
                "application/rss+xml",
                "application/atom+xml",
                "application/xml",
                "text/xml",
            ]

            if not any(valid_type in content_type for valid_type in valid_types):
                health.warnings.append(f"Unexpected content type: {content_type}")

        except requests.exceptions.Timeout:
            health.errors.append("Request timeout")
            return health
        except requests.exceptions.ConnectionError:
            health.errors.append("Connection error")
            return health
        except requests.exceptions.HTTPError as e:
            health.errors.append(f"HTTP error: {e}")
            return health
        except Exception as e:
            health.errors.append(f"Network error: {str(e)}")
            return health

        # Parse feed content
        try:
            feed = self.parser.parse_feed(url)
            if feed:
                health.is_valid = True
                health.entry_count = len(feed.entries)
                health.feed_type = feed.feed_type
                health.last_updated = feed.last_updated

                # Validate feed quality
                self._check_feed_quality(feed, health)

            else:
                health.errors.append("Failed to parse feed content")

        except Exception as e:
            health.errors.append(f"Feed parsing error: {str(e)}")

        return health

    def _check_feed_quality(self, feed, health: FeedHealth):
        """Check feed quality and add warnings for common issues."""

        # Check for empty feed
        if not feed.entries:
            health.warnings.append("Feed has no entries")
            return

        # Check for old content
        latest_entry = max(feed.entries, key=lambda e: e.published or datetime.min, default=None)
        if latest_entry and latest_entry.published:
            days_old = (datetime.utcnow() - latest_entry.published).days
            if days_old > 90:
                health.warnings.append(f"Latest entry is {days_old} days old")

        # Check entry quality
        entries_without_description = sum(
            1 for entry in feed.entries if not entry.description and not entry.content
        )
        if entries_without_description > len(feed.entries) * 0.5:
            health.warnings.append("Many entries lack description/content")

        entries_without_date = sum(1 for entry in feed.entries if not entry.published)
        if entries_without_date > 0:
            health.warnings.append(f"{entries_without_date} entries lack publication dates")

        # Check for duplicate entries
        guids = [entry.guid for entry in feed.entries if entry.guid]
        if len(set(guids)) != len(guids):
            health.warnings.append("Feed contains duplicate entries")

    def generate_health_report(self, health_results: Dict[str, FeedHealth]) -> str:
        """Generate a human-readable health report."""

        if not health_results:
            return "No feeds to report on."

        total_feeds = len(health_results)
        valid_feeds = sum(1 for h in health_results.values() if h.is_valid)
        reachable_feeds = sum(1 for h in health_results.values() if h.is_reachable)

        report = [
            "=== FEED HEALTH REPORT ===",
            f"Total feeds checked: {total_feeds}",
            f"Valid feeds: {valid_feeds}/{total_feeds} ({valid_feeds/total_feeds*100:.1f}%)",
            f"Reachable feeds: {reachable_feeds}/{total_feeds} ({reachable_feeds/total_feeds*100:.1f}%)",
            "",
        ]

        # Group by status
        healthy_feeds = [h for h in health_results.values() if h.is_valid and not h.errors]
        warning_feeds = [h for h in health_results.values() if h.is_valid and h.warnings]
        broken_feeds = [h for h in health_results.values() if not h.is_valid or h.errors]

        if healthy_feeds:
            report.append("✅ HEALTHY FEEDS:")
            for health in healthy_feeds:
                report.append(f"  • {health.url} ({health.entry_count} entries)")
            report.append("")

        if warning_feeds:
            report.append("⚠️  FEEDS WITH WARNINGS:")
            for health in warning_feeds:
                report.append(f"  • {health.url}")
                for warning in health.warnings:
                    report.append(f"    - {warning}")
            report.append("")

        if broken_feeds:
            report.append("❌ BROKEN FEEDS:")
            for health in broken_feeds:
                report.append(f"  • {health.url}")
                for error in health.errors:
                    report.append(f"    - {error}")
            report.append("")

        return "\n".join(report)
