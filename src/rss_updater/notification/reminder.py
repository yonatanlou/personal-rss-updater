"""Handles sending reminders for feed-based blogs."""

from datetime import datetime, timedelta
from typing import List

from ..core import AppConfig, Post
from ..storage import BlogStorage
from . import EmailNotifier


def send_reminder_for_feed_blogs(config: AppConfig, storage: BlogStorage, blogs: List[dict]):
    """Sends consolidated reminder for blogs with the 'feed' monitoring strategy."""
    print("Checking for feed-based blogs that need reminders...")

    # Find all feed blogs that need reminders
    feed_blogs_needing_reminders = []

    for blog in blogs:
        if blog.get("monitoring_strategy") == "feed":
            blog_name = blog["name"]
            blog_state = storage.get_blog_state(blog_name)

            # Check if this blog needs a reminder (no reminder sent or last one was >2 weeks ago)
            needs_reminder = (
                not blog_state
                or not blog_state.last_reminder_sent
                or (datetime.now() - blog_state.last_reminder_sent) > timedelta(weeks=2)
            )

            if needs_reminder:
                feed_blogs_needing_reminders.append(blog)

    # If we have blogs needing reminders, send one consolidated email
    if feed_blogs_needing_reminders:
        print(
            f"  -> Sending consolidated reminder for {len(feed_blogs_needing_reminders)} feed blogs"
        )

        # Create a single consolidated reminder post
        post = Post(
            title="Manual Check Reminder for Feed Blogs",
            url="",  # No single URL for consolidated reminder
            blog_name="Feed Blogs Reminder",
            content=f"Please manually check these {len(feed_blogs_needing_reminders)} blogs:\n"
            + "\n".join(
                [f"• {blog['name']}: {blog['url']}" for blog in feed_blogs_needing_reminders]
            ),
        )

        notifier = EmailNotifier(config)
        success = notifier.send_single_post(post)

        if success:
            # Mark all blogs as having received a reminder
            for blog in feed_blogs_needing_reminders:
                storage.update_last_reminder_sent(blog["name"])

            # Save the storage updates
            storage.save()
            print(f"  ✅ Reminder sent for {len(feed_blogs_needing_reminders)} blogs")
        else:
            print("  ❌ Failed to send consolidated reminder")
    else:
        print("  ✓ No feed blogs need reminders at this time")
