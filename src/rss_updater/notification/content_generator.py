"""Email content generation for RSS notifications."""

from datetime import datetime
from typing import List
from ..core import Post


class ContentGenerator:
    """Generates email content for RSS notifications."""
    
    def create_subject(self, new_posts: List[Post], stats: dict) -> str:
        """Create email subject line."""
        count = len(new_posts)
        date = datetime.now().strftime("%Y-%m-%d")
        
        if count == 0:
            return f"RSS Digest {date} - No new posts"
        elif count == 1:
            return f"RSS Digest {date} - 1 new post"
        else:
            return f"RSS Digest {date} - {count} new posts"
    
    def create_html_content(self, new_posts: List[Post], stats: dict, failed_blogs_summary: str) -> str:
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
    
    def create_text_content(self, new_posts: List[Post], stats: dict, failed_blogs_summary: str) -> str:
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
    
    def create_test_html(self, config) -> str:
        """Create test email HTML content."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ color: #007acc; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
                .content {{ padding: 20px 0; }}
                .footer {{ border-top: 1px solid #eee; padding-top: 10px; color: #666; font-size: 12px; }}
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
                    <li>SMTP Server: {config.email.smtp_server}:{config.email.smtp_port}</li>
                    <li>Recipient: {config.email.recipient}</li>
                    <li>Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                </ul>
            </div>
            <div class="footer">
                Generated by Personal RSS Updater
            </div>
        </body>
        </html>
        """
    
    def create_test_text(self, config) -> str:
        """Create test email plain text content."""
        return f"""
RSS UPDATER TEST EMAIL

This is a test email to verify that your RSS Updater email configuration is working correctly.

✅ If you're reading this, your email setup is working!

Configuration details:
- SMTP Server: {config.email.smtp_server}:{config.email.smtp_port}
- Recipient: {config.email.recipient}
- Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Generated by Personal RSS Updater
        """