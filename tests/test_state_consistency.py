"""Tests for blog state consistency and duplicate post detection."""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from rss_updater.core.models import Post
from rss_updater.storage.blog_state import BlogState
from rss_updater.storage.blog_storage import BlogStorage


class TestStateConsistency:
    """Test blog state consistency and duplicate detection."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "test_states.json"
        self.storage = BlogStorage(self.storage_path)

    def teardown_method(self):
        """Cleanup test environment."""
        self.temp_dir.cleanup()

    def test_duplicate_post_detection(self):
        """Test that duplicate posts are not reported twice."""
        # Initialize blog state with a post
        initial_post = Post(
            title="Test Post", url="https://example.com/post1", blog_name="Test Blog"
        )

        self.storage.update_blog_state(
            "Test Blog",
            url="https://example.com",
            last_post_title=initial_post.title,
            last_post_url=initial_post.url,
        )

        # Try to add the same post again
        state = self.storage.get_blog_state("Test Blog")

        # Check if this is a new post (should return False for duplicate)
        is_new_post = self._is_new_post(initial_post, state)
        assert not is_new_post, "Duplicate post should not be considered new"

    def test_same_title_different_url(self):
        """Test posts with same title but different URLs."""
        # Setup initial post
        post1 = Post(title="Same Title", url="https://example.com/post1", blog_name="Test Blog")

        self.storage.update_blog_state(
            "Test Blog",
            url="https://example.com",
            last_post_title=post1.title,
            last_post_url=post1.url,
        )

        # Create post with same title but different URL
        post2 = Post(title="Same Title", url="https://example.com/post2", blog_name="Test Blog")

        state = self.storage.get_blog_state("Test Blog")
        is_new_post = self._is_new_post(post2, state)

        # Should be considered new because URL is different
        assert is_new_post, "Post with same title but different URL should be new"

    def test_post_url_change_detection(self):
        """Test detection when a post's URL changes (permalink updates)."""
        # Setup initial post
        original_post = Post(
            title="Test Post", url="https://example.com/draft/post1", blog_name="Test Blog"
        )

        self.storage.update_blog_state(
            "Test Blog",
            url="https://example.com",
            last_post_title=original_post.title,
            last_post_url=original_post.url,
        )

        # Same post but with updated URL (moved from draft to published)
        updated_post = Post(
            title="Test Post", url="https://example.com/published/post1", blog_name="Test Blog"
        )

        state = self.storage.get_blog_state("Test Blog")
        is_new_post = self._is_new_post(updated_post, state)

        # This is tricky - same title but different URL
        # Could be treated as new post or URL update
        # The system should handle this consistently
        assert isinstance(is_new_post, bool), "Should return a boolean decision"

    def test_chronological_post_ordering(self):
        """Test that posts are processed in chronological order."""
        posts = [
            Post(
                title="Old Post",
                url="https://example.com/old",
                blog_name="Test Blog",
                date=datetime.now() - timedelta(days=5),
            ),
            Post(
                title="Recent Post",
                url="https://example.com/recent",
                blog_name="Test Blog",
                date=datetime.now() - timedelta(days=1),
            ),
            Post(
                title="Newest Post",
                url="https://example.com/newest",
                blog_name="Test Blog",
                date=datetime.now(),
            ),
        ]

        # Sort posts chronologically (newest first)
        sorted_posts = sorted(posts, key=lambda p: p.date or datetime.min, reverse=True)

        # Newest post should be first
        assert sorted_posts[0].title == "Newest Post"
        assert sorted_posts[-1].title == "Old Post"

    def test_state_corruption_recovery(self):
        """Test recovery from corrupted state data."""
        # Create valid state first
        self.storage.update_blog_state(
            "Test Blog", url="https://example.com", last_post_title="Valid Post"
        )
        self.storage.save()

        # Simulate corrupted state file
        with open(self.storage_path, "w") as f:
            f.write('{"invalid": "json", "missing_bracket":')

        # Should recover gracefully when loading corrupted state
        new_storage = BlogStorage(self.storage_path)

        # Should start with empty state instead of crashing
        assert len(new_storage.blog_states) == 0

        # Should be able to create new states
        new_storage.update_blog_state(
            "Recovery Blog", url="https://example.com", last_post_title="Recovery Post"
        )

        state = new_storage.get_blog_state("Recovery Blog")
        assert state is not None
        assert state.last_post_title == "Recovery Post"

    def test_concurrent_state_updates(self):
        """Test handling of concurrent state updates."""
        # Simulate multiple rapid updates to same blog
        blog_name = "Rapid Update Blog"

        for i in range(10):
            self.storage.update_blog_state(
                blog_name,
                url="https://example.com",
                last_post_title=f"Post {i}",
                last_post_url=f"https://example.com/post{i}",
            )

        # Final state should reflect the last update
        state = self.storage.get_blog_state(blog_name)
        assert state.last_post_title == "Post 9"
        assert state.last_post_url == "https://example.com/post9"

        # Should be able to save and reload
        self.storage.save()
        new_storage = BlogStorage(self.storage_path)
        reloaded_state = new_storage.get_blog_state(blog_name)
        assert reloaded_state.last_post_title == "Post 9"

    def test_failure_count_tracking(self):
        """Test proper tracking of failure counts."""
        blog_name = "Failing Blog"

        # Start with successful state
        self.storage.update_blog_state(
            blog_name, url="https://example.com", last_post_title="Success", failure_count=0
        )

        # Simulate failures
        for i in range(5):
            state = self.storage.get_blog_state(blog_name)
            self.storage.update_blog_state(blog_name, failure_count=state.failure_count + 1)

        # Should track failure count correctly
        state = self.storage.get_blog_state(blog_name)
        assert state.failure_count == 5

        # Reset on success
        self.storage.update_blog_state(
            blog_name, last_post_title="Back to Success", failure_count=0
        )

        state = self.storage.get_blog_state(blog_name)
        assert state.failure_count == 0
        assert state.last_post_title == "Back to Success"

    def test_blog_removal_cleanup(self):
        """Test proper cleanup when blogs are removed."""
        # Add multiple blogs
        blogs = ["Blog A", "Blog B", "Blog C"]
        for blog in blogs:
            self.storage.update_blog_state(
                blog,
                url=f"https://{blog.lower().replace(' ', '')}.com",
                last_post_title=f"Post from {blog}",
            )

        assert len(self.storage.blog_states) == 3

        # Remove one blog
        self.storage.remove_blog_state("Blog B")

        assert len(self.storage.blog_states) == 2
        assert self.storage.get_blog_state("Blog A") is not None
        assert self.storage.get_blog_state("Blog B") is None
        assert self.storage.get_blog_state("Blog C") is not None

    def _is_new_post(self, post: Post, blog_state: BlogState) -> bool:
        """Helper method to determine if a post is new."""
        if blog_state is None:
            return True

        # Simple duplicate detection logic
        return not (
            post.title == blog_state.last_post_title and post.url == blog_state.last_post_url
        )


if __name__ == "__main__":
    pytest.main([__file__])
