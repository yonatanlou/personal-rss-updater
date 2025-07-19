"""Data storage and persistence for the RSS updater application."""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .models import Post


@dataclass
class BlogState:
    """Tracks the state of a single blog."""
    
    blog_name: str
    url: str
    last_post_title: Optional[str] = None
    last_post_url: Optional[str] = None
    last_check: Optional[datetime] = None
    failure_count: int = 0
    last_success: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert blog state to dictionary for JSON serialization."""
        return {
            'blog_name': self.blog_name,
            'url': self.url,
            'last_post_title': self.last_post_title,
            'last_post_url': self.last_post_url,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'failure_count': self.failure_count,
            'last_success': self.last_success.isoformat() if self.last_success else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BlogState':
        """Create blog state from dictionary (JSON deserialization)."""
        last_check = None
        if data.get('last_check'):
            try:
                last_check = datetime.fromisoformat(data['last_check'])
            except ValueError:
                pass
        
        last_success = None
        if data.get('last_success'):
            try:
                last_success = datetime.fromisoformat(data['last_success'])
            except ValueError:
                pass
        
        return cls(
            blog_name=data['blog_name'],
            url=data['url'],
            last_post_title=data.get('last_post_title'),
            last_post_url=data.get('last_post_url'),
            last_check=last_check,
            failure_count=data.get('failure_count', 0),
            last_success=last_success
        )


class BlogStorage:
    """Manages persistent storage of blog states using JSON."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize storage with optional custom path."""
        self.storage_path = storage_path or Path("blog_states.json")
        self.blog_states: Dict[str, BlogState] = {}
        self._load()
    
    def _load(self) -> None:
        """Load blog states from JSON file."""
        if not self.storage_path.exists():
            self.blog_states = {}
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.blog_states = {}
            for blog_name, state_data in data.items():
                try:
                    self.blog_states[blog_name] = BlogState.from_dict(state_data)
                except Exception as e:
                    print(f"Warning: Failed to load state for blog '{blog_name}': {e}")
                    
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in storage file {self.storage_path}: {e}")
            self._create_backup()
            self.blog_states = {}
        except Exception as e:
            print(f"Warning: Failed to load storage file {self.storage_path}: {e}")
            self.blog_states = {}
    
    def _create_backup(self) -> None:
        """Create backup of corrupted storage file."""
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.backup')
            shutil.copy2(self.storage_path, backup_path)
            print(f"Created backup of corrupted storage file: {backup_path}")
    
    def save(self) -> None:
        """Save blog states to JSON file with automatic backup."""
        # Create backup before writing if file exists
        if self.storage_path.exists():
            backup_path = self.storage_path.with_suffix('.json.bak')
            shutil.copy2(self.storage_path, backup_path)
        
        # Convert blog states to dictionary format
        data = {}
        for blog_name, state in self.blog_states.items():
            data[blog_name] = state.to_dict()
        
        try:
            # Write to temporary file first, then rename for atomic operation
            temp_path = self.storage_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.rename(self.storage_path)
            
        except Exception as e:
            print(f"Error saving storage file: {e}")
            # Clean up temporary file if it exists
            temp_path = self.storage_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
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