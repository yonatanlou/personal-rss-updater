"""Utility functions for the RSS updater application."""

import re
from datetime import datetime
from typing import Optional, List
from urllib.parse import urljoin, urlparse


def validate_url(url: str) -> bool:
    """
    Validate if a string is a proper URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing fragments and ensuring proper format.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL string
    """
    if not url:
        return url
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Parse and reconstruct without fragment
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


def resolve_relative_url(base_url: str, relative_url: str) -> str:
    """
    Resolve a relative URL against a base URL.
    
    Args:
        base_url: The base URL
        relative_url: The relative URL to resolve
        
    Returns:
        Absolute URL
    """
    return urljoin(base_url, relative_url)


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common unwanted characters
    text = re.sub(r'[\r\n\t]', ' ', text)
    
    # Remove HTML entities (basic ones)
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    return text.strip()


def extract_excerpt(text: str, max_length: int = 200) -> str:
    """
    Extract a brief excerpt from text.
    
    Args:
        text: The text to extract from
        max_length: Maximum length of excerpt
        
    Returns:
        Brief excerpt
    """
    if not text:
        return ""
    
    cleaned = clean_text(text)
    
    if len(cleaned) <= max_length:
        return cleaned
    
    # Try to break at a sentence boundary
    sentences = re.split(r'[.!?]+', cleaned)
    excerpt = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(excerpt + sentence) + 1 <= max_length:
            if excerpt:
                excerpt += ". "
            excerpt += sentence
        else:
            break
    
    # If no complete sentences fit, just truncate
    if not excerpt:
        excerpt = cleaned[:max_length].rsplit(' ', 1)[0] + "..."
    elif not excerpt.endswith(('.', '!', '?')):
        excerpt += "..."
    
    return excerpt


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string in various formats.
    
    Args:
        date_str: The date string to parse
        
    Returns:
        Datetime object or None if parsing failed
    """
    if not date_str:
        return None
    
    # Clean the date string
    date_str = clean_text(date_str)
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',                    # 2023-12-25
        '%Y-%m-%dT%H:%M:%S',          # 2023-12-25T15:30:00
        '%Y-%m-%dT%H:%M:%SZ',         # 2023-12-25T15:30:00Z
        '%Y-%m-%d %H:%M:%S',          # 2023-12-25 15:30:00
        '%B %d, %Y',                  # December 25, 2023
        '%b %d, %Y',                  # Dec 25, 2023
        '%d %B %Y',                   # 25 December 2023
        '%d %b %Y',                   # 25 Dec 2023
        '%m/%d/%Y',                   # 12/25/2023
        '%d/%m/%Y',                   # 25/12/2023
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try to extract just the date part if it contains time info
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',       # YYYY-MM-DD
        r'(\w+ \d{1,2}, \d{4})',      # Month DD, YYYY
        r'(\d{1,2} \w+ \d{4})',       # DD Month YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                extracted = match.group(1)
                for fmt in formats:
                    try:
                        return datetime.strptime(extracted, fmt)
                    except ValueError:
                        continue
            except Exception:
                continue
    
    return None


def get_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: The URL to extract domain from
        
    Returns:
        Domain string
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain, False otherwise
    """
    return get_domain(url1) == get_domain(url2)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: The text to split
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    
    # Clean and filter
    result = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Ignore very short "sentences"
            result.append(sentence)
    
    return result