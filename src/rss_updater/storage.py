"""Data storage and persistence for the RSS updater application."""

# Import from the new storage module
from .storage import BlogState, BlogStorage

__all__ = ['BlogState', 'BlogStorage']