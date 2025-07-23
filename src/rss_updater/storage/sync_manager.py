"""Synchronization manager for blog configurations."""

import json
from pathlib import Path
from typing import Dict
from .blog_state import BlogState
from ..constants import BLOGS_CONFIG_PATH, LEGACY_BLOGS_PATH


class SyncManager:
    """Handles synchronization between blog states and configuration."""

    def sync_with_blogs_config(
        self, blog_states: Dict[str, BlogState], blogs_config_path: Path = None
    ) -> Dict:
        """
        Sync blog states with blogs.json configuration file.

        This makes blogs.json the source of truth by:
        - Removing blogs from states that are no longer in config
        - Adding new blogs from config to states
        - Updating URLs for existing blogs if they changed

        Args:
            blog_states: Current blog states dictionary
            blogs_config_path: Path to blogs.json file (defaults to ./blogs.json)

        Returns:
            Dict with sync summary: added, removed, updated, errors
        """
        blogs_config_path = blogs_config_path or (
            BLOGS_CONFIG_PATH if BLOGS_CONFIG_PATH.exists() else LEGACY_BLOGS_PATH
        )

        if not blogs_config_path.exists():
            raise FileNotFoundError(f"Blogs config file not found: {blogs_config_path}")

        # Load blogs configuration
        try:
            with open(blogs_config_path, "r") as f:
                blogs_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in blogs config file: {e}")

        # Track changes for summary
        added_blogs = []
        removed_blogs = []
        updated_blogs = []
        errors = []

        # Create mapping of config blogs by name
        config_blogs = {blog["name"]: blog["url"] for blog in blogs_config}

        # Remove blogs that are no longer in config
        current_blog_names = list(blog_states.keys())
        for blog_name in current_blog_names:
            if blog_name not in config_blogs:
                del blog_states[blog_name]
                removed_blogs.append(blog_name)

        # Add new blogs and update existing ones
        for blog in blogs_config:
            blog_name = blog["name"]
            blog_url = blog["url"]

            if blog_name in blog_states:
                # Check if URL changed
                current_state = blog_states[blog_name]
                if current_state.url != blog_url:
                    # URL changed - update it and reset post data since it's a different source
                    current_state.url = blog_url
                    current_state.last_post_title = None
                    current_state.last_post_url = None
                    current_state.failure_count = 0
                    updated_blogs.append(f"{blog_name} (URL: {blog_url})")
            else:
                # New blog - add it
                blog_states[blog_name] = BlogState(blog_name=blog_name, url=blog_url)
                added_blogs.append(f"{blog_name} ({blog_url})")

        return {
            "added": added_blogs,
            "removed": removed_blogs,
            "updated": updated_blogs,
            "errors": errors,
            "total_blogs": len(blog_states),
        }
