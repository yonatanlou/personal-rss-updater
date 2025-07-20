"""Main selector detector class."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from .selector_candidate import SelectorCandidate
from .pattern_detector import PatternDetector
from .content_analyzer import ContentAnalyzer
from .post_extractor import PostExtractor
from ..utils import get_domain


class SelectorDetector:
    """Detects blog post selectors automatically."""
    
    def __init__(self, manual_selectors_file: Optional[Path] = None):
        self.manual_selectors_file = manual_selectors_file or Path("manual_selectors.json")
        self.manual_selectors = self._load_manual_selectors()
        
        # Initialize detection components
        self.pattern_detector = PatternDetector()
        self.content_analyzer = ContentAnalyzer()
        self.post_extractor = PostExtractor()
    
    def _load_manual_selectors(self) -> Dict:
        """Load manual selector overrides from JSON file."""
        if not self.manual_selectors_file.exists():
            return {}
        
        try:
            with open(self.manual_selectors_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load manual selectors: {e}")
            return {}
    
    def _get_manual_selector(self, url: str, blog_name: str = None) -> Optional[Dict]:
        """Get manual selector for a blog by URL or name."""
        # Try by blog name first
        if blog_name and blog_name in self.manual_selectors:
            return self.manual_selectors[blog_name]
        
        # Try by domain
        domain = get_domain(url)
        if domain in self.manual_selectors:
            return self.manual_selectors[domain]
        
        # Try by full URL
        if url in self.manual_selectors:
            return self.manual_selectors[url]
        
        return None
    
    def detect_post_selectors(self, soup: BeautifulSoup, base_url: str) -> List[SelectorCandidate]:
        """
        Detect potential post selectors on a page.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of selector candidates sorted by confidence
        """
        candidates = []
        
        # Method 1: Look for common post patterns
        candidates.extend(self.pattern_detector.detect_by_class_patterns(soup))
        
        # Method 2: Look for repeating structures
        candidates.extend(self.pattern_detector.detect_by_structure(soup))
        
        # Method 3: Look for elements with links
        candidates.extend(self.content_analyzer.detect_by_links(soup, base_url))
        
        # Sort by confidence and remove duplicates
        unique_candidates = self._deduplicate_candidates(candidates)
        return sorted(unique_candidates, key=lambda x: x.confidence, reverse=True)
    
    def get_latest_post(self, soup: BeautifulSoup, base_url: str, blog_name: str = None) -> Optional[Dict[str, str]]:
        """
        Get the latest post from a page using manual selectors or automatic detection.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            blog_name: Optional blog name for manual selector lookup
            
        Returns:
            Dictionary with post info or None if not found
        """
        # First try manual selectors
        manual_config = self._get_manual_selector(base_url, blog_name)
        if manual_config:
            return self.post_extractor.extract_with_manual_selectors(soup, base_url, manual_config)
        
        # Fall back to automatic detection
        candidates = self.detect_post_selectors(soup, base_url)
        
        if not candidates:
            return None
        
        # Use the best candidate
        best_candidate = candidates[0]
        
        if not best_candidate.elements:
            return None
        
        # Get the first (latest) post
        latest_element = best_candidate.elements[0]
        
        # Extract post information
        title = self.post_extractor.extract_post_title(latest_element)
        url = self.post_extractor.extract_post_url(latest_element, base_url)
        
        if title and len(title.strip()) > 5:  # Must have a reasonable title
            return {
                'title': title.strip(),
                'url': url or base_url,
                'selector': best_candidate.selector,
                'confidence': best_candidate.confidence
            }
        
        return None
    
    def _deduplicate_candidates(self, candidates: List[SelectorCandidate]) -> List[SelectorCandidate]:
        """Remove duplicate candidates."""
        seen_selectors = set()
        unique_candidates = []
        
        for candidate in candidates:
            if candidate.selector not in seen_selectors:
                seen_selectors.add(candidate.selector)
                unique_candidates.append(candidate)
        
        return unique_candidates