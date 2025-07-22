"""Feed data models."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class FeedEntry(BaseModel):
    """Represents a single feed entry/post."""

    title: str
    link: HttpUrl
    description: Optional[str] = None
    published: Optional[datetime] = None
    guid: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.title} ({self.link})"


class Feed(BaseModel):
    """Represents an RSS/Atom feed."""

    title: str
    link: HttpUrl
    description: Optional[str] = None
    language: Optional[str] = None
    last_updated: Optional[datetime] = None
    etag: Optional[str] = None
    modified: Optional[datetime] = None
    entries: List[FeedEntry] = Field(default_factory=list)
    feed_type: Optional[str] = None  # 'rss', 'atom', etc.
    version: Optional[str] = None  # RSS version or Atom version

    def __str__(self) -> str:
        return f"{self.title} ({len(self.entries)} entries)"
