"""Application constants and configuration paths."""

from pathlib import Path

# Configuration paths
BLOGS_CONFIG_PATH = Path("config/app/blogs.json")
APP_CONFIG_PATH = Path("config/app/config.yaml")
MANUAL_SELECTORS_PATH = Path("config/app/manual_selectors.json")

# Data storage paths
BLOG_STATES_PATH = Path("data/blog_states.json")
BLOG_STATES_BACKUP_PATH = Path("data/blog_states.json.bak")

# Default fallback paths (for backward compatibility)
LEGACY_BLOGS_PATH = Path("blogs.json")
LEGACY_BLOG_STATES_PATH = Path("blog_states.json")
