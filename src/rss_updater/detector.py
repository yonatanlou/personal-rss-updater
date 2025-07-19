"""Intelligent selector detection for blog post extraction."""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from .utils import clean_text, resolve_relative_url, get_domain


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


class SelectorDetector:
    """Detects blog post selectors automatically."""
    
    def __init__(self, manual_selectors_file: Optional[Path] = None):
        self.manual_selectors_file = manual_selectors_file or Path("manual_selectors.json")
        self.manual_selectors = self._load_manual_selectors()
        
        self.common_post_patterns = [
            # Common class patterns
            r'\.post\b', r'\.entry\b', r'\.article\b', r'\.blog-post\b',
            r'\.content\b', r'\.item\b', r'\.story\b', r'\.news\b',
            
            # ID patterns  
            r'#post\b', r'#entry\b', r'#article\b',
            
            # Element patterns
            r'^article$', r'^section$',
        ]
        
        self.title_patterns = [
            r'\.title\b', r'\.post-title\b', r'\.entry-title\b',
            r'\.headline\b', r'\.header\b',
            r'^h[1-6]$',
        ]
    
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
        candidates.extend(self._detect_by_class_patterns(soup))
        
        # Method 2: Look for repeating structures
        candidates.extend(self._detect_by_structure(soup))
        
        # Method 3: Look for elements with links
        candidates.extend(self._detect_by_links(soup, base_url))
        
        # Sort by confidence and remove duplicates
        unique_candidates = self._deduplicate_candidates(candidates)
        return sorted(unique_candidates, key=lambda x: x.confidence, reverse=True)
    
    def _detect_by_class_patterns(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """Detect posts using common class/id patterns."""
        candidates = []
        
        for pattern in self.common_post_patterns:
            # Find elements matching the pattern
            if pattern.startswith('.'):
                # Class pattern
                class_name = pattern[1:]  # Remove the dot
                elements = soup.find_all(class_=re.compile(class_name, re.I))
            elif pattern.startswith('#'):
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
    
    def _detect_by_structure(self, soup: BeautifulSoup) -> List[SelectorCandidate]:
        """Detect posts by finding repeating structures."""
        candidates = []
        
        # Look for multiple similar elements
        tag_counters = Counter()
        class_counters = Counter()
        
        for elem in soup.find_all(['div', 'article', 'section', 'li']):
            if elem.get('class'):
                for cls in elem.get('class'):
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
    
    def _detect_by_links(self, soup: BeautifulSoup, base_url: str) -> List[SelectorCandidate]:
        """Detect posts by looking for elements with internal links."""
        candidates = []
        
        # Find elements containing links that look like blog posts
        elements_with_links = []
        
        for elem in soup.find_all(['div', 'article', 'section', 'li']):
            links = elem.find_all('a', href=True)
            internal_links = [
                link for link in links 
                if self._is_internal_link(link.get('href'), base_url)
            ]
            
            if internal_links and self._looks_like_post_element(elem):
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
    
    def _calculate_confidence(self, elements: List[Tag], pattern: str) -> float:
        """Calculate confidence score for a set of elements."""
        if not elements:
            return 0.0
        
        base_score = 0.5
        
        # Bonus for good patterns
        if any(keyword in pattern.lower() for keyword in ['post', 'entry', 'article']):
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
        content_score = sum(1 for elem in elements[:5] if self._looks_like_post_element(elem))
        base_score += (content_score / min(5, len(elements))) * 0.2
        
        return min(1.0, max(0.0, base_score))
    
    def _looks_like_posts(self, elements: List[Tag]) -> bool:
        """Check if elements look like blog posts."""
        if not elements or len(elements) > 50:  # Too many probably not posts
            return False
        
        # Check if elements have post-like characteristics
        post_indicators = 0
        for elem in elements[:5]:  # Check first few
            if self._looks_like_post_element(elem):
                post_indicators += 1
        
        return post_indicators >= min(2, len(elements))
    
    def _looks_like_post_element(self, elem: Tag) -> bool:
        """Check if an element looks like a blog post."""
        text = elem.get_text().strip()
        
        # Must have reasonable amount of text
        if len(text) < 20:
            return False
        
        # Check for links
        links = elem.find_all('a')
        has_internal_links = any(link.get('href') for link in links)
        
        # Check for headings
        has_headings = bool(elem.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        
        # Check for time/date elements
        has_date = bool(elem.find(['time']) or 
                       re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', text))
        
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
    
    def _is_internal_link(self, href: str, base_url: str) -> bool:
        """Check if a link is internal to the site."""
        if not href:
            return False
        
        # Relative links are internal
        if not href.startswith(('http://', 'https://')):
            return True
        
        # Same domain
        from urllib.parse import urlparse
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
        if element.get('class'):
            classes = element.get('class')
            # Prefer classes that look like post-related
            post_classes = [cls for cls in classes 
                          if any(keyword in cls.lower() 
                               for keyword in ['post', 'entry', 'article', 'item'])]
            if post_classes:
                selectors.append(f".{post_classes[0]}")
            else:
                selectors.append(f".{classes[0]}")
        
        # Add ID if present and looks meaningful
        if element.get('id'):
            element_id = element.get('id')
            if any(keyword in element_id.lower() 
                  for keyword in ['post', 'entry', 'article']):
                selectors.append(f"#{element_id}")
        
        # Return the most specific reasonable selector
        if len(selectors) > 1:
            return "".join(selectors)
        else:
            return selectors[0] if selectors else element.name
    
    def _deduplicate_candidates(self, candidates: List[SelectorCandidate]) -> List[SelectorCandidate]:
        """Remove duplicate candidates."""
        seen_selectors = set()
        unique_candidates = []
        
        for candidate in candidates:
            if candidate.selector not in seen_selectors:
                seen_selectors.add(candidate.selector)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
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
            return self._extract_with_manual_selectors(soup, base_url, manual_config)
        
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
        title = self._extract_post_title(latest_element)
        url = self._extract_post_url(latest_element, base_url)
        
        if title and len(title.strip()) > 5:  # Must have a reasonable title
            return {
                'title': title.strip(),
                'url': url or base_url,
                'selector': best_candidate.selector,
                'confidence': best_candidate.confidence
            }
        
        return None
    
    def _extract_with_manual_selectors(self, soup: BeautifulSoup, base_url: str, config: Dict) -> Optional[Dict[str, str]]:
        """Extract latest post using manual selector configuration."""
        try:
            post_container = config.get('post_container')
            title_selector = config.get('title_selector')
            link_selector = config.get('link_selector')
            
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
                title_elem = latest_container.select_one(title_selector)
                if not title_elem:
                    # Try title selector on the container itself
                    if latest_container.name == title_selector or any(cls in title_selector for cls in latest_container.get('class', [])):
                        title_elem = latest_container
                
                if title_elem:
                    title = clean_text(title_elem.get_text())
            
            # Extract URL
            post_url = base_url  # Default to base URL
            if link_selector:
                link_elem = latest_container.select_one(link_selector)
                if link_elem and link_elem.get('href'):
                    post_url = resolve_relative_url(base_url, link_elem.get('href'))
            
            if title and len(title.strip()) > 5:
                return {
                    'title': title.strip(),
                    'url': post_url,
                    'selector': f"Manual: {post_container}",
                    'confidence': 1.0  # Manual selectors get full confidence
                }
            
            return None
            
        except Exception as e:
            print(f"  - Error with manual selectors: {e}")
            return None
    
    def _extract_post_title(self, element: Tag) -> Optional[str]:
        """Extract title from a post element."""
        # Try various title selectors in order of preference
        title_selectors = [
            'h1', 'h2', 'h3', 'h4',
            '.post-title', '.entry-title', '.title',
            'a[href]',
            '.headline', '.header'
        ]
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                if len(title) > 5:  # Must be reasonable length
                    return title
        
        return None
    
    def _extract_post_url(self, element: Tag, base_url: str) -> Optional[str]:
        """Extract URL from a post element."""
        # Look for links in order of preference
        link_selectors = [
            'h1 a[href]', 'h2 a[href]', 'h3 a[href]',
            '.post-title a[href]', '.entry-title a[href]',
            'a[href]'
        ]
        
        for selector in link_selectors:
            link_elem = element.select_one(selector)
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if self._is_internal_link(href, base_url):
                    return resolve_relative_url(base_url, href)
        
        return None