"""Main entry point for the Personal RSS Updater application."""

import sys
import argparse
from pathlib import Path
from typing import NoReturn
from dotenv import load_dotenv

from .core import load_config, create_sample_config
from .storage import BlogStorage
from .web import WebScraper
from .initializer import initialize_blog_states
from .monitoring import analyze_failed_blogs, analyze_blog_structure, test_manual_selector, BlogMonitor
from .emailer import EmailNotifier
import os


def main() -> NoReturn:
    """Main entry point for the RSS updater application."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Personal RSS Updater")
    parser.add_argument('command', nargs='?', default='run', 
                       choices=['run', 'init', 'sync', 'analyze', 'test-selector', 'check', 'test-email'], 
                       help='Command to execute (default: run)')
    parser.add_argument('--mark-as-read', action='store_true', default=True,
                       help='Mark current posts as already read during init')
    parser.add_argument('--url', help='URL to analyze or test (for analyze/test-selector commands)')
    parser.add_argument('--selector', help='CSS selector to test (for test-selector command)')
    parser.add_argument('--blog-name', help='Blog name for analysis')
    
    args = parser.parse_args()
    
    print("RSS Updater starting...")
    print("Personal RSS Updater v0.1.0")
    print("Monitoring blogs for new posts and sending daily digest notifications")
    
    if args.command == 'init':
        print("\n=== INITIALIZATION MODE ===")
        try:
            initialize_blog_states(mark_as_read=args.mark_as_read)
            print("Blog initialization completed successfully!")
        except Exception as e:
            print(f"Initialization failed: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif args.command == 'sync':
        print("\n=== SYNC MODE ===")
        print("Synchronizing blog states with blogs.json...")
        try:
            storage = BlogStorage()
            sync_result = storage.sync_with_blogs_config()
            
            print(f"\n✅ Sync completed successfully!")
            print(f"Total blogs after sync: {sync_result['total_blogs']}")
            
            if sync_result['added']:
                print(f"\n📥 Added {len(sync_result['added'])} blogs:")
                for blog in sync_result['added']:
                    print(f"  + {blog}")
            
            if sync_result['removed']:
                print(f"\n📤 Removed {len(sync_result['removed'])} blogs:")
                for blog in sync_result['removed']:
                    print(f"  - {blog}")
            
            if sync_result['updated']:
                print(f"\n🔄 Updated {len(sync_result['updated'])} blogs:")
                for blog in sync_result['updated']:
                    print(f"  ↻ {blog}")
            
            if sync_result['errors']:
                print(f"\n❌ Errors during sync:")
                for error in sync_result['errors']:
                    print(f"  ! {error}")
                sys.exit(1)
            
            if not any([sync_result['added'], sync_result['removed'], sync_result['updated']]):
                print("\n📊 No changes detected - blog states already in sync!")
                
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif args.command == 'analyze':
        print("\n=== ANALYSIS MODE ===")
        if args.url:
            analyze_blog_structure(args.url, args.blog_name)
        else:
            analyze_failed_blogs()
        sys.exit(0)
    
    elif args.command == 'test-selector':
        print("\n=== SELECTOR TESTING MODE ===")
        if not args.url or not args.selector:
            print("Error: --url and --selector are required for test-selector command")
            sys.exit(1)
        test_manual_selector(args.url, args.selector)
        sys.exit(0)
    
    elif args.command == 'check':
        print("\n=== MONITORING MODE ===")
        # Load config for monitoring mode
        config_path = Path("config.yaml")
        if not config_path.exists():
            print("❌ Configuration file not found. Run 'init' first.")
            sys.exit(1)
        
        try:
            config = load_config(config_path)
            
            # Show email configuration for check mode
            if config.email.username and config.email.password:
                print(f"Email credentials available:")
                print(f"- Sender username (from env): {config.email.username}")
                print(f"- Recipient (from config): {config.email.recipient}")
            else:
                print("⚠️  Email credentials not set - email notifications disabled")
            
            monitor = BlogMonitor(config)
            results = monitor.check_all_blogs()
            
            # Print summary
            print("\n" + monitor.get_summary())
            
            failed_summary = monitor.get_failed_blogs_summary()
            if failed_summary:
                print(failed_summary)
            
        except Exception as e:
            print(f"❌ Monitoring failed: {e}")
            sys.exit(1)
        sys.exit(0)
    
    elif args.command == 'test-email':
        print("\n=== EMAIL TESTING MODE ===")
        # Load config for email testing
        config_path = Path("config.yaml")
        if not config_path.exists():
            print("❌ Configuration file not found. Run 'init' first.")
            sys.exit(1)
        
        try:
            config = load_config(config_path)
            
            # Show email configuration being used
            print(f"Email credentials:")
            print(f"- Sender username (from env): {config.email.username}")
            print(f"- Recipient (from config): {config.email.recipient}")
            print(f"- Password set: {'Yes' if config.email.password else 'No'}")
            
            if not config.email.username or not config.email.password:
                print("❌ Missing email credentials. Set EMAIL_USERNAME and EMAIL_PASSWORD environment variables.")
                sys.exit(1)
            
            emailer = EmailNotifier(config)
            success = emailer.send_test_email()
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            sys.exit(1)
    
    config_path = Path("config.yaml")
    
    try:
        # Try to load configuration
        if not config_path.exists():
            print(f"\nConfiguration file not found: {config_path}")
            print("Creating sample configuration...")
            create_sample_config(config_path)
            print("Please edit config.yaml and set EMAIL_USERNAME and EMAIL_PASSWORD environment variables.")
            sys.exit(1)
        
        config = load_config(config_path)
        if not config.email.username:
            config.email.username = os.getenv('EMAIL_USERNAME')
        if not config.email.password:
            config.email.password = os.getenv('EMAIL_PASSWORD')
        # Print loaded configuration (with sensitive data masked)
        print("\nConfiguration loaded successfully:")
        print(f"- Email recipient: {config.email.recipient}")
        print(f"- SMTP server: {config.email.smtp_server}:{config.email.smtp_port}")
        print(f"- Blogs configured: {len(config.blogs)}")
        print(f"- Retry count: {config.retry_count}")
        print(f"- Failure threshold: {config.failure_threshold}")
        
        # Check email credentials and show what's being used
        print(f"\nEmail credentials:")
        print(f"- Sender username (from env): {config.email.username}")
        print(f"- Recipient (from config): {config.email.recipient}")
        print(f"- Password set: {'Yes' if config.email.password else 'No'}")
        
        # Check for required environment variables
        if not config.email.username:
            print("\nWARNING: EMAIL_USERNAME environment variable not set!")
        if not config.email.password:
            print("WARNING: EMAIL_PASSWORD environment variable not set!")
            
        if not config.email.username or not config.email.password:
            print("Please set the required environment variables and try again.")
            sys.exit(1)
            
        print("\nConfiguration validation successful!")
        
        # Initialize and test storage system
        print("\nInitializing storage system...")
        storage = BlogStorage()
        summary = storage.get_summary()
        
        print(f"Storage summary:")
        print(f"- Storage path: {summary['storage_path']}")
        print(f"- Total blogs tracked: {summary['total_blogs']}")
        print(f"- Failed blogs: {summary['failed_blogs']}")
        print(f"- Latest check: {summary['latest_check'] or 'Never'}")
        
        print("\nStorage system initialized successfully!")
        
        
        # Full workflow: Check for new posts and send email if found
        print("\n=== RUNNING FULL WORKFLOW ===")
        monitor = BlogMonitor(config)
        results = monitor.check_all_blogs()
        
        # Print monitoring summary
        print("\n" + monitor.get_summary())
        
        # Get failed blogs summary
        failed_summary = monitor.get_failed_blogs_summary()
        if failed_summary:
            print(failed_summary)
        
        # Send email if there are new posts or failed blogs
        new_posts = results.get('new_posts', [])
        if new_posts or failed_summary:
            print("\n=== SENDING EMAIL DIGEST ===")
            print(f"Email will be sent:")
            print(f"- From: {config.email.username} (sender from env)")
            print(f"- To: {config.email.recipient} (recipient from config)")
            print(f"- SMTP: {config.email.smtp_server}:{config.email.smtp_port}")
            
            emailer = EmailNotifier(config)
            email_success = emailer.send_digest(new_posts, results['stats'], failed_summary)
            
            if email_success:
                print("✅ Daily digest sent successfully!")
            else:
                print("❌ Failed to send daily digest")
        else:
            print("\n📧 No email sent - no new posts and no failed blogs")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()