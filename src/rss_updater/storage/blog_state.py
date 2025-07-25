"""Blog state data structure."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class BlogState:
    """Tracks the state of a single blog."""

    blog_name: str
    url: str
    last_post_title: Optional[str] = None
    last_post_url: Optional[str] = None
    last_check: Optional[datetime] = None
    failure_count: int = 0
    last_success: Optional[datetime] = None
    last_reminder_sent: Optional[datetime] = None
    is_problematic: bool = False

    # RSS/Feed specific fields
    feed_url: Optional[str] = None
    feed_etag: Optional[str] = None
    feed_modified: Optional[datetime] = None
    last_post_date: Optional[datetime] = None  # Publication date of last post

    def to_dict(self) -> Dict:
        """Convert blog state to dictionary for JSON serialization."""
        return {
            "blog_name": self.blog_name,
            "url": self.url,
            "last_post_title": self.last_post_title,
            "last_post_url": self.last_post_url,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "failure_count": self.failure_count,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_reminder_sent": (
                self.last_reminder_sent.isoformat() if self.last_reminder_sent else None
            ),
            "is_problematic": self.is_problematic,
            "feed_url": self.feed_url,
            "feed_etag": self.feed_etag,
            "feed_modified": self.feed_modified.isoformat() if self.feed_modified else None,
            "last_post_date": self.last_post_date.isoformat() if self.last_post_date else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BlogState":
        """Create blog state from dictionary (JSON deserialization)."""
        last_check = None
        if data.get("last_check"):
            try:
                last_check = datetime.fromisoformat(data["last_check"])
            except ValueError:
                pass

        last_success = None
        if data.get("last_success"):
            try:
                last_success = datetime.fromisoformat(data["last_success"])
            except ValueError:
                pass

        last_reminder_sent = None
        if data.get("last_reminder_sent"):
            try:
                last_reminder_sent = datetime.fromisoformat(data["last_reminder_sent"])
            except ValueError:
                pass

        feed_modified = None
        if data.get("feed_modified"):
            try:
                feed_modified = datetime.fromisoformat(data["feed_modified"])
            except ValueError:
                pass

        last_post_date = None
        if data.get("last_post_date"):
            try:
                last_post_date = datetime.fromisoformat(data["last_post_date"])
            except ValueError:
                pass

        return cls(
            blog_name=data["blog_name"],
            url=data["url"],
            last_post_title=data.get("last_post_title"),
            last_post_url=data.get("last_post_url"),
            last_check=last_check,
            failure_count=data.get("failure_count", 0),
            last_success=last_success,
            last_reminder_sent=last_reminder_sent,
            is_problematic=data.get("is_problematic", False),
            feed_url=data.get("feed_url"),
            feed_etag=data.get("feed_etag"),
            feed_modified=feed_modified,
            last_post_date=last_post_date,
        )
