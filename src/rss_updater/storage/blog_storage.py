"""Main blog storage class."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from .blog_state import BlogState
from .file_manager import FileManager
from .sync_manager import SyncManager
from ..core import Post


class BlogStorage:
    """Manages persistent storage of blog states using JSON."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize storage with optional custom path."""
        self.storage_path = storage_path or Path("blog_states.json")
        self.file_manager = FileManager(self.storage_path)
        self.sync_manager = SyncManager()
        self.blog_states: Dict[str, BlogState] = {}
        self._load()
    
    def _load(self) -> None:
        """Load blog states from JSON file."""
        data = self.file_manager.load_data()
        
        self.blog_states = {}
        for blog_name, state_data in data.items():
            try:
                self.blog_states[blog_name] = BlogState.from_dict(state_data)
            except Exception as e:
                print(f"Warning: Failed to load state for blog '{blog_name}': {e}")
    
    def save(self) -> None:
        """Save blog states to JSON file with automatic backup."""
        # Convert blog states to dictionary format
        data = {}
        for blog_name, state in self.blog_states.items():
            data[blog_name] = state.to_dict()
        
        try:
            self.file_manager.save_data(data)
        except Exception as e:
            print(f"Error saving storage file: {e}")
            raise
    
    def get_blog_state(self, blog_name: str) -> Optional[BlogState]:
        """Get the state for a specific blog."""
        return self.blog_states.get(blog_name)
    
    def update_blog_state(self, blog_name: str, **kwargs) -> None:
        """Update or create blog state with given parameters."""
        current_state = self.blog_states.get(blog_name)
        
        if current_state:
            # Update existing state
            for key, value in kwargs.items():
                if hasattr(current_state, key):
                    setattr(current_state, key, value)
        else:
            # Create new state
            state_data = {
                'blog_name': blog_name,
                'url': kwargs.get('url', ''),
                'last_post_title': kwargs.get('last_post_title'),
                'last_post_url': kwargs.get('last_post_url'),
                'last_check': kwargs.get('last_check'),
                'failure_count': kwargs.get('failure_count', 0),
                'last_success': kwargs.get('last_success')
            }
            self.blog_states[blog_name] = BlogState(**state_data)
    
    def update_latest_post(self, blog_name: str, post: Post) -> None:
        """Update the latest post for a blog."""
        self.update_blog_state(
            blog_name,
            last_post_title=post.title,
            last_post_url=post.url,
            last_check=datetime.now(),
            last_success=datetime.now()
        )
    
    def increment_failure_count(self, blog_name: str, url: str = '') -> None:
        """Increment failure count for a blog."""
        current_state = self.get_blog_state(blog_name)
        failure_count = (current_state.failure_count + 1) if current_state else 1
        
        self.update_blog_state(
            blog_name,
            url=url,
            failure_count=failure_count,
            last_check=datetime.now()
        )
    
    def reset_failure_count(self, blog_name: str) -> None:
        """Reset failure count for a blog."""
        self.update_blog_state(blog_name, failure_count=0)
    
    def get_failed_blogs(self, threshold: int = 3) -> Dict[str, BlogState]:
        """Get blogs that have failed more than the threshold."""
        return {
            name: state for name, state in self.blog_states.items()
            if state.failure_count >= threshold
        }
    
    def get_summary(self) -> Dict:
        """Get summary statistics of stored blog states."""
        total_blogs = len(self.blog_states)
        failed_blogs = len(self.get_failed_blogs())
        
        last_checks = [
            state.last_check for state in self.blog_states.values()
            if state.last_check
        ]
        latest_check = max(last_checks) if last_checks else None
        
        return {
            'total_blogs': total_blogs,
            'failed_blogs': failed_blogs,
            'latest_check': latest_check,
            'storage_path': str(self.storage_path)
        }
    
    def sync_with_blogs_config(self, blogs_config_path: Optional[Path] = None) -> Dict:
        """
        Sync blog states with blogs.json configuration file.
        
        Args:
            blogs_config_path: Path to blogs.json file (defaults to ./blogs.json)
            
        Returns:
            Dict with sync summary: added, removed, updated, errors
        """
        try:
            result = self.sync_manager.sync_with_blogs_config(
                self.blog_states, blogs_config_path
            )
            # Save the synchronized states
            self.save()
            return result
        except Exception as e:
            result = {
                'added': [],
                'removed': [], 
                'updated': [],
                'errors': [f"Failed to sync with blogs config: {e}"],
                'total_blogs': len(self.blog_states)
            }
            return result
    
    def get_blogs_needing_biweekly_reminder(self) -> Dict[str, BlogState]:
        """
        Get blogs that need bi-weekly reminders due to persistent failures.
        
        Returns blogs that:
        - Have been marked as problematic OR have 5+ consecutive failures
        - Haven't had a reminder sent in the last 14 days
        
        Returns:
            Dictionary of blog names to BlogState objects needing reminders
        """
        now = datetime.now()
        two_weeks_ago = now - timedelta(days=14)
        
        reminder_needed = {}
        
        for blog_name, state in self.blog_states.items():
            # Check if blog qualifies for reminder
            needs_reminder = (
                state.is_problematic or 
                state.failure_count >= 5
            )
            
            if not needs_reminder:
                continue
            
            # Check if reminder was sent recently
            if state.last_reminder_sent and state.last_reminder_sent > two_weeks_ago:
                continue  # Too recent
            
            reminder_needed[blog_name] = state
        
        return reminder_needed
    
    def mark_reminder_sent(self, blog_name: str) -> None:
        """Mark that a reminder was sent for a problematic blog."""
        if blog_name in self.blog_states:
            self.blog_states[blog_name].last_reminder_sent = datetime.now()
    
    def mark_as_problematic(self, blog_name: str, is_problematic: bool = True) -> None:
        """Mark a blog as problematic (or unmark it)."""
        if blog_name in self.blog_states:
            self.blog_states[blog_name].is_problematic = is_problematic