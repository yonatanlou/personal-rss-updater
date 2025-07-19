"""Initialize blog states with current latest posts as already read."""

import json
from pathlib import Path
from typing import List, Dict

from .scraper import WebScraper
from .storage import BlogStorage
from .models import Post
from .detector import SelectorDetector


def load_blogs_from_json(blogs_file: Path = None) -> List[Dict[str, str]]:
    """Load blog list from JSON file."""
    if blogs_file is None:
        blogs_file = Path("blogs.json")
    
    if not blogs_file.exists():
        raise FileNotFoundError(f"Blog list file not found: {blogs_file}")
    
    with open(blogs_file, 'r') as f:
        blogs = json.load(f)
    
    return blogs


def initialize_blog_states(blogs_file: Path = None, mark_as_read: bool = True) -> None:
    """
    Initialize blog states by fetching current latest posts.
    
    Args:
        blogs_file: Path to JSON file with blog list
        mark_as_read: If True, mark current posts as already read
    """
    print("Initializing blog states...")
    
    # Load blog list
    blogs = load_blogs_from_json(blogs_file)
    print(f"Found {len(blogs)} blogs to initialize")
    
    # Initialize storage and detector
    storage = BlogStorage()
    detector = SelectorDetector()
    
    # Initialize scraper
    with WebScraper() as scraper:
        for i, blog in enumerate(blogs, 1):
            blog_name = blog['name']
            blog_url = blog['url']
            
            print(f"[{i}/{len(blogs)}] Processing: {blog_name}")
            
            try:
                # Check if already initialized
                existing_state = storage.get_blog_state(blog_name)
                if existing_state and existing_state.last_post_title:
                    print(f"  - Already initialized, skipping")
                    continue
                
                # Fetch the page to get latest post info
                soup = scraper.fetch_and_parse(blog_url)
                if not soup:
                    print(f"  - Failed to fetch page")
                    storage.increment_failure_count(blog_name, blog_url)
                    continue
                
                # Use intelligent post detection (with blog name for manual selectors)
                latest_post_info = detector.get_latest_post(soup, blog_url, blog_name)
                
                if latest_post_info:
                    title = latest_post_info['title']
                    url = latest_post_info['url']
                    confidence = latest_post_info['confidence']
                    
                    if mark_as_read:
                        # Create post object for the latest post
                        latest_post = Post(
                            title=title,
                            url=url,
                            blog_name=blog_name
                        )
                        storage.update_latest_post(blog_name, latest_post)
                        print(f"  - Found latest post: {title[:60]}... (confidence: {confidence:.2f})")
                    else:
                        storage.update_blog_state(
                            blog_name,
                            url=blog_url,
                            last_post_title=None,
                            last_post_url=None
                        )
                        print(f"  - Detected post: {title[:60]}... (not marked as read)")
                else:
                    # Fallback to page title
                    page_title = soup.find('title')
                    if page_title:
                        title_text = page_title.get_text().strip()
                        print(f"  - Could not detect posts, using page title: {title_text[:60]}...")
                        
                        if mark_as_read:
                            fallback_post = Post(
                                title=f"Fallback - {title_text}",
                                url=blog_url,
                                blog_name=blog_name
                            )
                            storage.update_latest_post(blog_name, fallback_post)
                        else:
                            storage.update_blog_state(blog_name, url=blog_url)
                    else:
                        print(f"  - Could not find any content")
                        storage.update_blog_state(blog_name, url=blog_url)
                    
            except Exception as e:
                print(f"  - Error: {e}")
                storage.increment_failure_count(blog_name, blog_url)
    
    # Save all states
    storage.save()
    
    # Print summary
    summary = storage.get_summary()
    print(f"\nInitialization complete!")
    print(f"- Total blogs: {summary['total_blogs']}")
    print(f"- Failed blogs: {summary['failed_blogs']}")
    print(f"- Storage saved to: {summary['storage_path']}")


if __name__ == "__main__":
    initialize_blog_states(mark_as_read=True)