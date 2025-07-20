"""Email sending functionality with retry logic."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
from ..core import AppConfig


class EmailSender:
    """Handles email sending with retry logic."""
    
    def __init__(self, config: AppConfig):
        """Initialize email sender with configuration."""
        self.config = config
    
    def send_email(self, subject: str, html_content: str, text_content: str) -> bool:
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