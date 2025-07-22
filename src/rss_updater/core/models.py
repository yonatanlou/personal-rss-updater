"""Data models for the RSS updater application."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Post:
    """Represents a blog post."""

    title: str
    url: str
    blog_name: str
    date: Optional[datetime] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    published_date: Optional[datetime] = None  # For RSS feeds
    author: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert post to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "blog_name": self.blog_name,
            "date": self.date.isoformat() if self.date else None,
            "excerpt": self.excerpt,
            "content": self.content,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Post":
        """Create post from dictionary (JSON deserialization)."""
        date = None
        if data.get("date"):
            try:
                date = datetime.fromisoformat(data["date"])
            except ValueError:
                pass  # Keep date as None if parsing fails

        published_date = None
        if data.get("published_date"):
            try:
                published_date = datetime.fromisoformat(data["published_date"])
            except ValueError:
                pass  # Keep published_date as None if parsing fails

        return cls(
            title=data["title"],
            url=data["url"],
            blog_name=data["blog_name"],
            date=date,
            excerpt=data.get("excerpt"),
            content=data.get("content"),
            published_date=published_date,
            author=data.get("author"),
        )


@dataclass
class Blog:
    """Represents a blog configuration."""

    name: str
    url: str
    selectors: Dict[str, str]
    enabled: bool = True

    def to_dict(self) -> Dict:
        """Convert blog to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "selectors": self.selectors,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Blog":
        """Create blog from dictionary (JSON deserialization)."""
        return cls(
            name=data["name"],
            url=data["url"],
            selectors=data.get("selectors", {}),
            enabled=data.get("enabled", True),
        )
