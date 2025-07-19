"""Email notification system for the RSS updater."""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from time import sleep

from .config import AppConfig
from .models import Post


class EmailNotifier:
    """Handles email notifications for new blog posts."""
    
    def __init__(self, config: AppConfig):
        """Initialize email notifier with configuration."""
        self.config = config
        self.smtp_server = None
    
    def send_digest(self, new_posts: List[Post], stats: dict, failed_blogs_summary: str = "") -> bool:
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
            subject = self._create_subject(new_posts, stats)
            html_content = self._create_html_content(new_posts, stats, failed_blogs_summary)
            text_content = self._create_text_content(new_posts, stats, failed_blogs_summary)
            
            # Send email
            success = self._send_email(subject, html_content, text_content)
            
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
            html_content = self._create_test_html()
            text_content = self._create_test_text()
            
            success = self._send_email(subject, html_content, text_content)
            
            if success:
                print(f"✅ Test email sent successfully to {self.config.email.recipient}")
            else:
                print("❌ Failed to send test email")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending test email: {e}")
            return False
    
    def _create_subject(self, new_posts: List[Post], stats: dict) -> str:
        """Create email subject line."""
        count = len(new_posts)
        date = datetime.now().strftime("%Y-%m-%d")
        
        if count == 0:
            return f"RSS Digest {date} - No new posts"
        elif count == 1:
            return f"RSS Digest {date} - 1 new post"
        else:
            return f"RSS Digest {date} - {count} new posts"
    
    def _create_html_content(self, new_posts: List[Post], stats: dict, failed_blogs_summary: str) -> str:
        """Create HTML email content."""
        date = datetime.now().strftime("%B %d, %Y")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RSS Digest</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                .header {{
                    border-bottom: 2px solid #007acc;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #007acc;
                    margin: 0;
                    font-size: 28px;
                }}
                .date {{
                    color: #666;
                    font-size: 16px;
                    margin-top: 5px;
                }}
                .summary {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 30px;
                }}
                .post {{
                    margin-bottom: 25px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }}
                .post:last-child {{
                    border-bottom: none;
                }}
                .post-title {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                .post-title a {{
                    color: #007acc;
                    text-decoration: none;
                }}
                .post-title a:hover {{
                    text-decoration: underline;
                }}
                .blog-name {{
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .post-url {{
                    font-size: 12px;
                    color: #888;
                    word-break: break-all;
                }}
                .no-posts {{
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    padding: 40px 20px;
                }}
                .failed-blogs {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 30px;
                }}
                .failed-blogs h3 {{
                    color: #856404;
                    margin-top: 0;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📰 RSS Digest</h1>
                <div class="date">{date}</div>
            </div>
            
            <div class="summary">
                <strong>Summary:</strong> {len(new_posts)} new posts from {stats.get('checked_blogs', 0)} blogs
            </div>
        """
        
        if new_posts:
            # Sort posts chronologically (newest first)
            sorted_posts = sorted(new_posts, key=lambda p: p.blog_name)
            
            for post in sorted_posts:
                html += f"""
                <div class="post">
                    <div class="blog-name">📖 {post.blog_name}</div>
                    <div class="post-title">
                        <a href="{post.url}">{post.title}</a>
                    </div>
                    <div class="post-url">{post.url}</div>
                </div>
                """
        else:
            html += """
            <div class="no-posts">
                No new posts today. All caught up! 🎉
            </div>
            """
        
        # Add failed blogs warning if any
        if failed_blogs_summary:
            html += f"""
            <div class="failed-blogs">
                <h3>⚠️ Blog Monitoring Issues</h3>
                <pre style="white-space: pre-wrap; font-family: inherit;">{failed_blogs_summary}</pre>
            </div>
            """
        
        html += """
            <div class="footer">
                Generated by Personal RSS Updater<br>
                🤖 Powered by intelligent web scraping
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_text_content(self, new_posts: List[Post], stats: dict, failed_blogs_summary: str) -> str:
        """Create plain text email content."""
        date = datetime.now().strftime("%B %d, %Y")
        
        lines = []
        lines.append(f"RSS DIGEST - {date}")
        lines.append("=" * 40)
        lines.append(f"Summary: {len(new_posts)} new posts from {stats.get('checked_blogs', 0)} blogs")
        lines.append("")
        
        if new_posts:
            lines.append("NEW POSTS:")
            lines.append("-" * 20)
            
            # Sort posts by blog name
            sorted_posts = sorted(new_posts, key=lambda p: p.blog_name)
            
            for post in sorted_posts:
                lines.append(f"📖 {post.blog_name}")
                lines.append(f"   {post.title}")
                lines.append(f"   {post.url}")
                lines.append("")
        else:
            lines.append("No new posts today. All caught up! 🎉")
            lines.append("")
        
        if failed_blogs_summary:
            lines.append(failed_blogs_summary)
        
        lines.append("")
        lines.append("Generated by Personal RSS Updater")
        lines.append("🤖 Powered by intelligent web scraping")
        
        return "\\n".join(lines)
    
    def _create_test_html(self) -> str:
        """Create test email HTML content."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { color: #007acc; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
                .content { padding: 20px 0; }
                .footer { border-top: 1px solid #eee; padding-top: 10px; color: #666; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 RSS Updater Test Email</h1>
            </div>
            <div class="content">
                <p>This is a test email to verify that your RSS Updater email configuration is working correctly.</p>
                <p><strong>✅ If you're reading this, your email setup is working!</strong></p>
                <p>Configuration details:</p>
                <ul>
                    <li>SMTP Server: {self.config.email.smtp_server}:{self.config.email.smtp_port}</li>
                    <li>Recipient: {self.config.email.recipient}</li>
                    <li>Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                </ul>
            </div>
            <div class="footer">
                Generated by Personal RSS Updater
            </div>
        </body>
        </html>
        """
    
    def _create_test_text(self) -> str:
        """Create test email plain text content."""
        return f"""
RSS UPDATER TEST EMAIL

This is a test email to verify that your RSS Updater email configuration is working correctly.

✅ If you're reading this, your email setup is working!

Configuration details:
- SMTP Server: {self.config.email.smtp_server}:{self.config.email.smtp_port}
- Recipient: {self.config.email.recipient}
- Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Generated by Personal RSS Updater
        """
    
    def _send_email(self, subject: str, html_content: str, text_content: str) -> bool:
        """
        Send email with retry logic.
        
        Args:
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.config.email.username
                msg['To'] = self.config.email.recipient
                
                # Attach text and HTML parts
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                html_part = MIMEText(html_content, 'html', 'utf-8')
                
                msg.attach(text_part)
                msg.attach(html_part)
                
                # Send email
                with smtplib.SMTP(self.config.email.smtp_server, self.config.email.smtp_port) as server:
                    server.starttls()
                    server.login(self.config.email.username, self.config.email.password)
                    server.send_message(msg)
                
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP Authentication failed: {e}")
                return False  # Don't retry auth failures
                
            except (smtplib.SMTPException, ConnectionError) as e:
                print(f"❌ SMTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False
                
            except Exception as e:
                print(f"❌ Unexpected email error: {e}")
                return False
        
        return False