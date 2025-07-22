"""Content analysis for blog post detection."""

import re
from typing import List
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

from .selector_candidate import SelectorCandidate


class ContentAnalyzer:
    """Analyzes content to determine if elements are blog posts."""

    def looks_like_post_element(self, elem: Tag) -> bool:
        """Check if an element looks like a blog post."""
        text = elem.get_text().strip()

        # Must have reasonable amount of text
        if len(text) < 20:
            return False

        # Check for links
        links = elem.find_all("a")
        has_internal_links = any(link.get("href") for link in links)

        # Check for headings
        has_headings = bool(elem.find(["h1", "h2", "h3", "h4", "h5", "h6"]))

        # Check for time/date elements
        has_date = bool(
            elem.find(["time"]) or re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", text)
        )

        # Score based on indicators
        score = 0
        if has_internal_links:
            score += 1
        if has_headings:
            score += 1
        if has_date:
            score += 1
        if len(text) > 100:
            score += 1

        return score >= 2

    def detect_by_links(self, soup: BeautifulSoup, base_url: str) -> List[SelectorCandidate]:
        """Detect posts by looking for elements with internal links."""
        candidates = []

        # Find elements containing links that look like blog posts
        elements_with_links = []

        for elem in soup.find_all(["div", "article", "section", "li"]):
            links = elem.find_all("a", href=True)
            internal_links = [
                link for link in links if self._is_internal_link(link.get("href"), base_url)
            ]

            if internal_links and self.looks_like_post_element(elem):
                elements_with_links.append(elem)

        if len(elements_with_links) >= 2:
            # Group by similar selectors
            grouped = self._group_similar_elements(elements_with_links)
            for group in grouped:
                if len(group) >= 2:
                    confidence = min(0.9, len(group) / 10)
                    selector = self._create_selector(group[0])
                    candidates.append(SelectorCandidate(selector, confidence, group))

        return candidates

    def _is_internal_link(self, href: str, base_url: str) -> bool:
        """Check if a link is internal to the site."""
        if not href:
            return False

        # Relative links are internal
        if not href.startswith(("http://", "https://")):
            return True

        # Same domain
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(href).netloc

        return base_domain == link_domain

    def _group_similar_elements(self, elements: List[Tag]) -> List[List[Tag]]:
        """Group elements with similar selectors."""
        groups = {}

        for elem in elements:
            selector = self._create_selector(elem)
            if selector not in groups:
                groups[selector] = []
            groups[selector].append(elem)

        return [group for group in groups.values() if len(group) >= 2]

    def _create_selector(self, element: Tag) -> str:
        """Create a CSS selector for an element."""
        # Try to create a specific but not overly specific selector
        selectors = []

        # Add tag name
        selectors.append(element.name)

        # Add most specific class
        if element.get("class"):
            classes = element.get("class")
            # Prefer classes that look like post-related
            post_classes = [
                cls
                for cls in classes
                if any(keyword in cls.lower() for keyword in ["post", "entry", "article", "item"])
            ]
            if post_classes:
                selectors.append(f".{post_classes[0]}")
            else:
                selectors.append(f".{classes[0]}")

        # Add ID if present and looks meaningful
        if element.get("id"):
            element_id = element.get("id")
            if any(keyword in element_id.lower() for keyword in ["post", "entry", "article"]):
                selectors.append(f"#{element_id}")

        # Return the most specific reasonable selector
        if len(selectors) > 1:
            return "".join(selectors)
        else:
            return selectors[0] if selectors else element.name
