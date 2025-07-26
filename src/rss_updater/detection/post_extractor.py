"""Post extraction functionality."""

from typing import Optional, Dict, List
from bs4 import BeautifulSoup, Tag
from ..utils import clean_text, resolve_relative_url
from ..core.models import Post


class PostExtractor:
    """Extracts post information from HTML elements."""

    def extract_post_title(self, element: Tag) -> Optional[str]:
        """Extract title from a post element."""
        # Try various title selectors in order of preference
        title_selectors = [
            "h1",
            "h2",
            "h3",
            "h4",
            ".post-title",
            ".entry-title",
            ".title",
            "a[href]",
            ".headline",
            ".header",
        ]

        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                if len(title) > 5:  # Must be reasonable length
                    return title

        return None

    def extract_post_url(self, element: Tag, base_url: str) -> Optional[str]:
        """Extract URL from a post element."""
        # Look for links in order of preference
        link_selectors = [
            "h1 a[href]",
            "h2 a[href]",
            "h3 a[href]",
            ".post-title a[href]",
            ".entry-title a[href]",
            "a[href]",
        ]

        for selector in link_selectors:
            link_elem = element.select_one(selector)
            if link_elem and link_elem.get("href"):
                href = link_elem.get("href")
                if self._is_internal_link(href, base_url):
                    return resolve_relative_url(base_url, href)

        return None

    def extract_with_manual_selectors(
        self, soup: BeautifulSoup, base_url: str, config: Dict
    ) -> Optional[Dict[str, str]]:
        """Extract latest post using manual selector configuration."""
        try:
            post_container = config.get("post_container")
            title_selector = config.get("title_selector")
            link_selector = config.get("link_selector")

            # Find post containers
            containers = soup.select(post_container)
            if not containers:
                print(f"  - Manual selector '{post_container}' found no containers")
                return None

            # Get the first (latest) container
            latest_container = containers[0]

            # Extract title
            title = None
            if title_selector:
                if title_selector == "self":
                    # Use the container itself as the title element
                    title_elem = latest_container
                else:
                    title_elem = latest_container.select_one(title_selector)
                    if not title_elem:
                        # Try title selector on the container itself
                        if latest_container.name == title_selector or any(
                            cls in title_selector for cls in latest_container.get("class", [])
                        ):
                            title_elem = latest_container

                if title_elem:
                    title = clean_text(title_elem.get_text())

            # Extract URL
            post_url = base_url  # Default to base URL
            if link_selector:
                if link_selector == "self":
                    # Use the container itself as the link element
                    link_elem = latest_container
                else:
                    link_elem = latest_container.select_one(link_selector)

                if link_elem and link_elem.get("href"):
                    post_url = resolve_relative_url(base_url, link_elem.get("href"))

            if title and len(title.strip()) > 5:
                return {
                    "title": title.strip(),
                    "url": post_url,
                    "selector": f"Manual: {post_container}",
                    "confidence": 1.0,  # Manual selectors get full confidence
                }

            return None

        except Exception as e:
            print(f"  - Error with manual selectors: {e}")
            return None

    def _is_internal_link(self, href: str, base_url: str) -> bool:
        """Check if a link is internal to the site."""
        if not href:
            return False

        # Relative links are internal
        if not href.startswith(("http://", "https://")):
            return True

        # Same domain
        from urllib.parse import urlparse

        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(href).netloc

        return base_domain == link_domain

    def extract_posts(
        self, soup: BeautifulSoup, selector: str, base_url: str, blog_name: str
    ) -> List[Post]:
        """Extract posts from HTML soup using the given selector."""
        posts = []
        elements = soup.select(selector)

        for element in elements:
            # Extract title
            title = self.extract_post_title(element)
            if not title:
                continue

            # Extract URL
            post_url = self.extract_post_url(element, base_url)
            if not post_url:
                post_url = base_url  # Fallback to base URL

            # Create Post object
            post = Post(title=title, url=post_url, blog_name=blog_name)
            posts.append(post)

        return posts
