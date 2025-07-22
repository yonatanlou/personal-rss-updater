"""Utility functions for the RSS updater application."""

import re
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
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

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
    text = re.sub(r"\s+", " ", text.strip())

    # Remove common unwanted characters
    text = re.sub(r"[\r\n\t]", " ", text)

    # Remove HTML entities (basic ones)
    html_entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&nbsp;": " ",
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
    sentences = re.split(r"[.!?]+", cleaned)
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
        excerpt = cleaned[:max_length].rsplit(" ", 1)[0] + "..."
    elif not excerpt.endswith((".", "!", "?")):
        excerpt += "..."

    return excerpt


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
