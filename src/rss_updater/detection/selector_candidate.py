"""Selector candidate class for blog post detection."""

from typing import List
from bs4 import Tag
from ..utils import clean_text


class SelectorCandidate:
    """Represents a potential CSS selector for blog posts."""
    
    def __init__(self, selector: str, confidence: float, elements: List[Tag]):
        self.selector = selector
        self.confidence = confidence
        self.elements = elements
        self.sample_titles = [self._extract_title(elem) for elem in elements[:3]]
    
    def _extract_title(self, element: Tag) -> str:
        """Extract title from an element."""
        # Try various title extraction methods
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.title', '.post-title', '.entry-title',
            'a', '.link'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                if len(title) > 10:  # Reasonable title length
                    return title
        
        # Fallback to element text
        text = clean_text(element.get_text())
        return text[:100] + "..." if len(text) > 100 else text