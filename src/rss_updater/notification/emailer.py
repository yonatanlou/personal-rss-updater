"""Main email notifier class."""

from typing import List
from ..core import AppConfig, Post
from .content_generator import ContentGenerator
from .reminder_generator import ReminderGenerator
from .email_sender import EmailSender


class EmailNotifier:
    """Handles email notifications for new blog posts."""

    def __init__(self, config: AppConfig):
        """Initialize email notifier with configuration."""
        self.config = config
        self.content_generator = ContentGenerator()
        self.reminder_generator = ReminderGenerator()
        self.email_sender = EmailSender(config)

    def send_digest(
        self, new_posts: List[Post], stats: dict, failed_blogs_summary: str = ""
    ) -> bool:
        """
        Send daily digest email with new posts.

        Args:
            new_posts: List of new posts found
            stats: Statistics from monitoring
            failed_blogs_summary: Summary of failed blogs

        Returns:
            True if email sent successfully, False otherwise
        """
        if not new_posts and not failed_blogs_summary:
            print("No new posts and no failed blogs - skipping email")
            return True

        try:
            # Create email message
            subject = self.content_generator.create_subject(new_posts, stats)
            html_content = self.content_generator.create_html_content(
                new_posts, stats, failed_blogs_summary
            )
            text_content = self.content_generator.create_text_content(
                new_posts, stats, failed_blogs_summary
            )

            # Send email
            success = self.email_sender.send_email(subject, html_content, text_content)

            if success:
                print(f"✅ Digest email sent successfully to {self.config.email.recipient}")
            else:
                print("❌ Failed to send digest email")

            return success

        except Exception as e:
            print(f"❌ Error sending digest email: {e}")
            return False

    def send_test_email(self) -> bool:
        """Send a test email to verify configuration."""
        try:
            subject = "RSS Updater - Test Email"
            html_content = self.content_generator.create_test_html(self.config)
            text_content = self.content_generator.create_test_text(self.config)

            success = self.email_sender.send_email(subject, html_content, text_content)

            if success:
                print(f"✅ Test email sent successfully to {self.config.email.recipient}")
            else:
                print("❌ Failed to send test email")

            return success

        except Exception as e:
            print(f"❌ Error sending test email: {e}")
            return False

    def send_biweekly_reminder(self, problematic_blogs: dict) -> bool:
        """
        Send bi-weekly reminder email about problematic blogs.

        Args:
            problematic_blogs: Dictionary of blog names to BlogState objects

        Returns:
            True if email sent successfully, False otherwise
        """
        if not problematic_blogs:
            print("No problematic blogs need reminders")
            return True

        try:
            subject = (
                f"RSS Monitor - Bi-weekly Reminder: {len(problematic_blogs)} blogs need attention"
            )
            html_content = self.reminder_generator.create_reminder_html(problematic_blogs)
            text_content = self.reminder_generator.create_reminder_text(problematic_blogs)

            success = self.email_sender.send_email(subject, html_content, text_content)

            if success:
                print(f"✅ Bi-weekly reminder sent for {len(problematic_blogs)} problematic blogs")
            else:
                print("❌ Failed to send bi-weekly reminder")

            return success

        except Exception as e:
            print(f"❌ Error sending bi-weekly reminder: {e}")
            return False

    def send_single_post(self, post: Post) -> bool:
        """Send a single post notification."""
        try:
            subject = f"{post.blog_name}: {post.title}"

            # Handle posts with content (like consolidated reminders)
            if hasattr(post, "content") and post.content:
                # Convert newlines to <br> for HTML and add proper formatting
                html_content_body = post.content.replace("\n", "<br>")
                html_content = (
                    f'<h1>{post.title}</h1><div style="margin: 20px 0;">{html_content_body}</div>'
                )
                text_content = f"{post.title}\n\n{post.content}"
            else:
                # Standard single post format
                html_content = f'<h1>{post.title}</h1><p><a href="{post.url}">Read more</a></p>'
                text_content = f"{post.title}\n{post.url}"

            success = self.email_sender.send_email(subject, html_content, text_content)

            if success:
                print(f"✅ Notification sent for {post.title}")
            else:
                print(f"❌ Failed to send notification for {post.title}")

            return success

        except Exception as e:
            print(f"❌ Error sending single post notification: {e}")
            return False
