"""Intelligent selector detection for blog post extraction."""

# Import from the new detection module
from .detection import SelectorCandidate, SelectorDetector

__all__ = ['SelectorCandidate', 'SelectorDetector']