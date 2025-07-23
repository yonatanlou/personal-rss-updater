#!/usr/bin/env python3
"""
Easy blog analysis script for debugging scrapers.

Usage:
    python debug_blog.py <blog_name_or_url>
    python debug_blog.py "Gwern.net Newsletter"
    python debug_blog.py https://gwern.net/
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rss_updater.web import WebScraper
from rss_updater.detection import SelectorDetector
from rss_updater.constants import BLOGS_CONFIG_PATH, MANUAL_SELECTORS_PATH


def load_blogs() -> List[Dict]:
    """Load blog configuration."""
    if BLOGS_CONFIG_PATH.exists():
        with open(BLOGS_CONFIG_PATH) as f:
            return json.load(f)
    return []


def load_manual_selectors() -> Dict:
    """Load manual selectors."""
    if MANUAL_SELECTORS_PATH.exists():
        with open(MANUAL_SELECTORS_PATH) as f:
            return json.load(f)
    return {}


def find_blog_by_name(name: str) -> Optional[Dict]:
    """Find blog by name."""
    blogs = load_blogs()
    for blog in blogs:
        if blog["name"].lower() == name.lower():
            return blog
    return None


def analyze_blog(blog_name_or_url: str):
    """Analyze a blog for scraping patterns."""
    # Determine if input is a name or URL
    if blog_name_or_url.startswith("http"):
        url = blog_name_or_url
        blog_name = "Unknown"
    else:
        blog = find_blog_by_name(blog_name_or_url)
        if not blog:
            print(f"❌ Blog '{blog_name_or_url}' not found in configuration")
            print("\nAvailable blogs:")
            blogs = load_blogs()
            for i, b in enumerate(blogs, 1):
                print(f"  {i}. {b['name']}")
            return
        url = blog["url"]
        blog_name = blog["name"]

    print(f"🔍 ANALYZING: {blog_name}")
    print(f"🌐 URL: {url}")
    print("=" * 60)

    # Fetch the page
    print("📥 Fetching page...")
    with WebScraper() as scraper:
        soup = scraper.fetch_and_parse(url)
        if not soup:
            print("❌ Failed to fetch page")
            return

    print("✅ Page fetched successfully")
    print(f"📄 Title: {soup.title.string if soup.title else 'No title'}")
    print()

    # Check manual selector if exists
    manual_selectors = load_manual_selectors()
    if blog_name in manual_selectors:
        print("🎯 MANUAL SELECTOR FOUND:")
        selector_config = manual_selectors[blog_name]
        print(f"   Description: {selector_config.get('description', 'N/A')}")
        print(f"   Container: {selector_config.get('post_container', 'N/A')}")
        print(f"   Title: {selector_config.get('title_selector', 'N/A')}")
        print(f"   Link: {selector_config.get('link_selector', 'N/A')}")

        # Test the manual selector
        link_selector = selector_config.get("link_selector", "")
        if link_selector:
            print(f"\n🧪 TESTING MANUAL SELECTOR: {link_selector}")
            elements = soup.select(link_selector)
            print(f"   Found {len(elements)} elements:")
            for i, elem in enumerate(elements[:5], 1):  # Show first 5
                title = elem.get_text(strip=True)[:60]
                href = elem.get("href", "No href")
                print(f"   {i}. {title}...")
                print(f"      URL: {href}")
            if len(elements) > 5:
                print(f"   ... and {len(elements) - 5} more")
        print()

    # Run automatic detection
    print("🤖 AUTOMATIC DETECTION:")
    detector = SelectorDetector()
    result = detector.get_latest_post(soup, url, blog_name)

    if result:
        print("✅ Automatic detection successful:")
        print(f"   Title: {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Confidence: {result['confidence']:.2f}")
    else:
        print("❌ Automatic detection failed")
    print()

    # Show potential selectors for debugging
    print("🔧 POTENTIAL SELECTORS TO TRY:")
    selectors_to_test = [
        "a[href*='blog']",
        "a[href*='post']",
        "a[href*='2024']",
        "a[href*='2025']",
        "h1 a",
        "h2 a",
        "h3 a",
        ".post a",
        ".entry a",
        ".article a",
        "article a",
        "main a",
    ]

    for selector in selectors_to_test:
        elements = soup.select(selector)
        if elements and len(elements) <= 10:  # Only show reasonable number of results
            print(f"   {selector} → {len(elements)} elements")
            for i, elem in enumerate(elements[:3], 1):  # Show first 3
                title = elem.get_text(strip=True)[:40]
                href = elem.get("href", "")
                if href and not href.startswith("#"):  # Skip anchor links
                    print(f"      {i}. {title}... → {href}")

    print("\n💡 TIPS:")
    print("   - Look for patterns in the URLs (e.g., /blog/, /posts/, year)")
    print("   - Check if there are specific classes or IDs for blog posts")
    print(
        "   - Test selectors with: python -m rss_updater.main test-selector --url URL --selector SELECTOR"
    )
    print("   - Update manual_selectors.json with working selectors")


def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_blog.py <blog_name_or_url>")
        print("\nExamples:")
        print("  python debug_blog.py 'Gwern.net Newsletter'")
        print("  python debug_blog.py https://gwern.net/")
        return

    blog_name_or_url = sys.argv[1]
    analyze_blog(blog_name_or_url)


if __name__ == "__main__":
    main()
