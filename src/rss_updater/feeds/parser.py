"""RSS/Atom feed parsing functionality."""

import feedparser
from typing import Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
from .models import Feed, FeedEntry


class FeedParser:
    """Parser for RSS and Atom feeds."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Personal RSS Updater)", timeout: int = 30):
        """Initialize feed parser."""
        self.user_agent = user_agent
        self.timeout = timeout

    def parse_feed(
        self, url: str, etag: Optional[str] = None, modified: Optional[datetime] = None
    ) -> Optional[Feed]:
        """
        Parse an RSS/Atom feed from URL.

        Args:
            url: Feed URL to parse
            etag: ETag header from previous request for caching
            modified: Last-Modified datetime from previous request for caching

        Returns:
            Feed object or None if parsing failed
        """
        try:
            # Use feedparser's built-in conditional request support

            # Use feedparser's built-in conditional request support
            kwargs = {
                "etag": etag,
                "modified": modified.timetuple() if modified else None,
            }

            # Parse the feed
            parsed = feedparser.parse(url, **{k: v for k, v in kwargs.items() if v is not None})

            # Check if feed was modified (not cached)
            if hasattr(parsed, "status"):
                if parsed.status == 304:  # Not Modified
                    return None
                elif parsed.status >= 400:  # Error
                    print(f"HTTP error {parsed.status} parsing feed {url}")
                    return None

            # Check for feed parsing errors
            if hasattr(parsed, "bozo") and parsed.bozo:
                if hasattr(parsed, "bozo_exception"):
                    print(f"Feed parsing warning for {url}: {parsed.bozo_exception}")

            # Extract feed metadata
            feed_info = parsed.feed

            feed_data = {
                "title": self._get_text_content(feed_info.get("title", "Untitled Feed")),
                "link": feed_info.get("link", url),
                "description": self._get_text_content(feed_info.get("description", "")),
                "language": feed_info.get("language"),
                "entries": [],
            }

            # Add caching headers
            if hasattr(parsed, "etag"):
                feed_data["etag"] = parsed.etag
            if hasattr(parsed, "modified"):
                feed_data["modified"] = datetime(*parsed.modified[:6]) if parsed.modified else None

            # Detect feed type and version
            if hasattr(parsed, "version"):
                feed_data["version"] = parsed.version
                if "atom" in parsed.version.lower():
                    feed_data["feed_type"] = "atom"
                elif "rss" in parsed.version.lower():
                    feed_data["feed_type"] = "rss"
                else:
                    feed_data["feed_type"] = "unknown"

            # Parse entries
            for entry in parsed.entries:
                feed_entry = self._parse_entry(entry)
                if feed_entry:
                    feed_data["entries"].append(feed_entry)

            # Set last updated time
            feed_data["last_updated"] = datetime.utcnow()

            return Feed(**feed_data)

        except Exception as e:
            print(f"Error parsing feed {url}: {e}")
            return None

    def _parse_entry(self, entry) -> Optional[FeedEntry]:
        """Parse a single feed entry."""
        try:
            entry_data = {
                "title": self._get_text_content(entry.get("title", "Untitled")),
                "link": entry.get("link", ""),
            }

            # Handle description/summary/content
            description = ""
            if hasattr(entry, "description"):
                description = self._get_text_content(entry.description)
            elif hasattr(entry, "summary"):
                description = self._get_text_content(entry.summary)

            entry_data["description"] = description

            # Handle content (often in Atom feeds)
            content = ""
            if hasattr(entry, "content") and entry.content:
                if isinstance(entry.content, list) and entry.content:
                    content = self._get_text_content(entry.content[0].get("value", ""))
                else:
                    content = self._get_text_content(entry.content)

            entry_data["content"] = content

            # Handle publication date
            published_date = None
            for date_field in ["published_parsed", "updated_parsed"]:
                if hasattr(entry, date_field):
                    date_tuple = getattr(entry, date_field)
                    if date_tuple:
                        try:
                            published_date = datetime(*date_tuple[:6])
                            break
                        except (ValueError, TypeError):
                            continue

            # Try string date fields as fallback
            if not published_date:
                for date_field in ["published", "updated"]:
                    if hasattr(entry, date_field):
                        date_str = getattr(entry, date_field)
                        if date_str:
                            try:
                                published_date = parsedate_to_datetime(date_str)
                                break
                            except (ValueError, TypeError):
                                continue

            entry_data["published"] = published_date

            # Handle GUID/ID
            guid = entry.get("id") or entry.get("guid")
            if isinstance(guid, dict):
                guid = guid.get("value", str(guid))
            entry_data["guid"] = str(guid) if guid else None

            # Handle author
            author = ""
            if hasattr(entry, "author"):
                author = entry.author
            elif hasattr(entry, "authors") and entry.authors:
                author = (
                    entry.authors[0].get("name", "")
                    if isinstance(entry.authors[0], dict)
                    else str(entry.authors[0])
                )

            entry_data["author"] = author

            return FeedEntry(**entry_data)

        except Exception as e:
            print(f"Error parsing feed entry: {e}")
            return None

    def _get_text_content(self, content) -> str:
        """Extract plain text from potentially HTML content."""
        if not content:
            return ""

        if isinstance(content, dict):
            content = content.get("value", str(content))

        content = str(content)

        # Basic HTML stripping (feedparser usually handles this)
        import re

        content = re.sub(r"<[^>]+>", "", content)
        content = content.replace("&nbsp;", " ")
        content = content.replace("&amp;", "&")
        content = content.replace("&lt;", "<")
        content = content.replace("&gt;", ">")
        content = content.replace("&quot;", '"')

        return content.strip()

    def validate_feed(self, url: str) -> bool:
        """
        Validate if a URL points to a valid RSS/Atom feed.

        Args:
            url: Feed URL to validate

        Returns:
            True if valid feed, False otherwise
        """
        try:
            feed = self.parse_feed(url)
            return feed is not None and len(feed.entries) >= 0
        except Exception:
            return False

    def get_feed_info(self, url: str) -> dict:
        """
        Get basic information about a feed without parsing all entries.

        Args:
            url: Feed URL to analyze

        Returns:
            Dictionary with feed information
        """
        info = {
            "url": url,
            "title": None,
            "description": None,
            "feed_type": None,
            "version": None,
            "entry_count": 0,
            "last_updated": None,
            "valid": False,
            "error": None,
        }

        try:
            feed = self.parse_feed(url)
            if feed:
                info.update(
                    {
                        "title": feed.title,
                        "description": feed.description,
                        "feed_type": feed.feed_type,
                        "version": feed.version,
                        "entry_count": len(feed.entries),
                        "last_updated": feed.last_updated,
                        "valid": True,
                    }
                )
            else:
                info["error"] = "Failed to parse feed"

        except Exception as e:
            info["error"] = str(e)

        return info
