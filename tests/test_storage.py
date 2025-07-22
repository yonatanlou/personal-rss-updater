"""Tests for the storage module."""

import tempfile
from datetime import datetime
from pathlib import Path

from rss_updater.core.models import Post
from rss_updater.storage.blog_state import BlogState
from rss_updater.storage.blog_storage import BlogStorage


def test_blog_state_serialization():
    """Test BlogState serialization and deserialization."""
    state = BlogState(
        blog_name="Test Blog",
        url="https://example.com",
        last_post_title="Test Post",
        last_post_url="https://example.com/post1",
        last_check=datetime.now(),
        failure_count=2,
    )

    # Test serialization
    data = state.to_dict()
    assert data["blog_name"] == "Test Blog"
    assert data["failure_count"] == 2

    # Test deserialization
    restored_state = BlogState.from_dict(data)
    assert restored_state.blog_name == state.blog_name
    assert restored_state.failure_count == state.failure_count


def test_blog_storage_operations():
    """Test basic BlogStorage operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_states.json"
        storage = BlogStorage(storage_path)

        # Test initial state
        assert len(storage.blog_states) == 0
        assert storage.get_blog_state("nonexistent") is None

        # Test creating new blog state
        storage.update_blog_state("Test Blog", url="https://example.com", last_post_title="Post 1")

        state = storage.get_blog_state("Test Blog")
        assert state is not None
        assert state.blog_name == "Test Blog"
        assert state.last_post_title == "Post 1"

        # Test updating existing state
        storage.update_blog_state("Test Blog", failure_count=3)
        state = storage.get_blog_state("Test Blog")
        assert state.failure_count == 3

        # Test save and reload
        storage.save()

        new_storage = BlogStorage(storage_path)
        state = new_storage.get_blog_state("Test Blog")
        assert state is not None
        assert state.failure_count == 3


def test_post_operations():
    """Test Post model operations."""
    post = Post(
        title="Test Post",
        url="https://example.com/post",
        blog_name="Test Blog",
        excerpt="This is a test post",
    )

    # Test serialization
    data = post.to_dict()
    assert data["title"] == "Test Post"
    assert data["blog_name"] == "Test Blog"

    # Test deserialization
    restored_post = Post.from_dict(data)
    assert restored_post.title == post.title
    assert restored_post.excerpt == post.excerpt


if __name__ == "__main__":
    test_blog_state_serialization()
    test_blog_storage_operations()
    test_post_operations()
    print("All storage tests passed!")
