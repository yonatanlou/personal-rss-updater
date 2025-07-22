"""Pattern-based detection methods for blog posts."""

import re
from collections import Counter
from typing import List
from bs4 import BeautifulSoup, Tag

from .selector_candidate import SelectorCandidate


class PatternDetector:
    """Detects blog posts using common patterns."""

    def __init__(self):
        self.common_post_patterns = [
            # Common class patterns
            r"\.post\b",
            r"\.entry\b",
            r"\.article\b",
            r"\.blog-post\b",
            r"\.content\b",
            r"\.item\b",
            r"\.story\b",
            r"\.news\b",
            # ID patterns
            r"#post\b",
            r"#entry\b",
            r"#article\b",
            # Element patterns
            r"^article$",
            r"^section$",
        ]

    def detect_by_class_patterns(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """Detect posts using common class/id patterns."""
        candidates = []

        for pattern in self.common_post_patterns:
            # Find elements matching the pattern
            if pattern.startswith(r"\."):
                # Class pattern - remove the escaped dot
                class_name = pattern[2:]  # Remove the \.
                elements = soup.find_all(class_=re.compile(class_name, re.I))
            elif pattern.startswith("#"):
                # ID pattern
                id_name = pattern[1:]  # Remove the hash
                elements = soup.find_all(id=re.compile(id_name, re.I))
            else:
                # Element pattern
                elements = soup.find_all(pattern)

            if elements and len(elements) >= 1:
                # Score based on number of matches and content quality
                confidence = self._calculate_confidence(elements, pattern)
                if confidence > 0.3:  # Minimum confidence threshold
                    selector = self._create_selector(elements[0])
                    candidates.append(SelectorCandidate(selector, confidence, elements))

        return candidates

    def detect_by_structure(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """Detect posts by finding repeating structures."""
        candidates = []

        # Look for multiple similar elements
        tag_counters = Counter()
        class_counters = Counter()

        for elem in soup.find_all(["div", "article", "section", "li"]):
            if elem.get("class"):
                for cls in elem.get("class"):
                    class_counters[cls] += 1
            tag_counters[elem.name] += 1

        # Find classes that appear multiple times
        for cls, count in class_counters.items():
            if 2 <= count <= 20:  # Reasonable range for blog posts
                elements = soup.find_all(class_=cls)
                if self._looks_like_posts(elements):
                    confidence = min(0.8, count / 10)  # Higher confidence for more posts
                    selector = f".{cls}"
                    candidates.append(SelectorCandidate(selector, confidence, elements))

        return candidates

    def _calculate_confidence(self, elements: List[Tag], pattern: str) -> float:
        """Calculate confidence score for a set of elements."""
        if not elements:
            return 0.0

        base_score = 0.5

        # Bonus for good patterns
        if any(keyword in pattern.lower() for keyword in ["post", "entry", "article"]):
            base_score += 0.3

        # Bonus for reasonable number of elements
        count = len(elements)
        if 2 <= count <= 10:
            base_score += 0.2
        elif count == 1:
            base_score += 0.1

        # Penalty for too many elements
        if count > 20:
            base_score -= 0.3

        # Bonus for elements with good content
        from .content_analyzer import ContentAnalyzer

        analyzer = ContentAnalyzer()
        content_score = sum(1 for elem in elements[:5] if analyzer.looks_like_post_element(elem))
        base_score += (content_score / min(5, len(elements))) * 0.2

        return min(1.0, max(0.0, base_score))

    def _looks_like_posts(self, elements: List[Tag]) -> bool:
        """Check if elements look like blog posts."""
        if not elements or len(elements) > 50:  # Too many probably not posts
            return False

        # Check if elements have post-like characteristics
        from .content_analyzer import ContentAnalyzer

        analyzer = ContentAnalyzer()

        post_indicators = 0
        for elem in elements[:5]:  # Check first few
            if analyzer.looks_like_post_element(elem):
                post_indicators += 1

        return post_indicators >= min(2, len(elements))

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
