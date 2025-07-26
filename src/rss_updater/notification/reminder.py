"""Handles sending reminders for feed-based blogs."""

from datetime import datetime, timedelta
from typing import List

from ..core import AppConfig, Post
from ..storage import BlogStorage
from . import EmailNotifier


def send_reminder_for_feed_blogs(config: AppConfig, storage: BlogStorage, blogs: List[dict]):
    """Sends reminders for blogs with the 'feed' monitoring strategy."""
    print("Checking for feed-based blogs that need reminders...")
    notifier = EmailNotifier(config)

    for blog in blogs:
        if blog.get("monitoring_strategy") == "feed":
            blog_name = blog["name"]
            blog_state = storage.get_blog_state(blog_name)

            if not blog_state.last_reminder_sent or (
                datetime.now() - blog_state.last_reminder_sent
            ) > timedelta(weeks=2):
                print(f"  -> Sending reminder for {blog_name}")
                post = Post(
                    title=f"{blog_name}: Manual Check Reminder",
                    url=blog["url"],
                    blog_name=blog_name,
                )
                notifier.send_single_post(post)
                storage.update_last_reminder_sent(blog_name)
