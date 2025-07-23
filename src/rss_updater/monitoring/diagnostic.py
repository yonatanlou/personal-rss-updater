"""Diagnostic tools for analyzing blog structure and selector detection."""

import json
from pathlib import Path

from ..web import WebScraper
from ..detection import SelectorDetector


def analyze_blog_structure(url: str, blog_name: str = None) -> None:
    """
    Analyze a blog's structure to help with manual selector tuning.

    Args:
        url: The blog URL to analyze
        blog_name: Optional blog name for display
    """
    print(f"\n{'=' * 60}")
    print(f"ANALYZING: {blog_name or url}")
    print(f"URL: {url}")
    print(f"{'=' * 60}")

    with WebScraper() as scraper:
        soup = scraper.fetch_and_parse(url)
        if not soup:
            print("❌ Failed to fetch page")
            return

        detector = SelectorDetector()

        # Get all candidates
        candidates = detector.detect_post_selectors(soup, url)

        print("\n📊 DETECTION RESULTS:")
        print(f"Found {len(candidates)} potential selectors")

        if not candidates:
            print("❌ No post selectors detected")
            print("\n🔍 MANUAL INSPECTION NEEDED:")
            print("Let's examine the page structure...")
            _manual_inspection(soup, url)
            return

        # Show all candidates
        for i, candidate in enumerate(candidates, 1):
            print(f"\n{i}. Selector: {candidate.selector}")
            print(f"   Confidence: {candidate.confidence:.2f}")
            print(f"   Elements found: {len(candidate.elements)}")
            print("   Sample titles:")
            for j, title in enumerate(candidate.sample_titles[:3], 1):
                print(f"     {j}. {title[:80]}...")

        # Test the best candidate
        best = candidates[0]
        print(f"\n🎯 TESTING BEST CANDIDATE: {best.selector}")

        latest_post = detector.get_latest_post(soup, url)
        if latest_post:
            print("✅ Latest post detected:")
            print(f"   Title: {latest_post['title']}")
            print(f"   URL: {latest_post['url']}")
            print(f"   Confidence: {latest_post['confidence']:.2f}")
        else:
            print("❌ Could not extract latest post with best selector")
            print("\n🔧 SUGGESTED MANUAL SELECTORS:")
            _suggest_manual_selectors(soup, url)


def _manual_inspection(soup, url: str) -> None:
    """Perform manual inspection when automatic detection fails."""

    # Look for common post-related elements
    print("\n🔍 SEARCHING FOR POST-LIKE ELEMENTS:")

    # Check for articles
    articles = soup.find_all("article")
    if articles:
        print(f"   📄 Found {len(articles)} <article> elements")
        for i, article in enumerate(articles[:3], 1):
            title = _extract_text_sample(article)
            print(f"     {i}. {title[:60]}...")

    # Check for common post classes
    post_classes = ["post", "entry", "blog-post", "article", "content-item"]
    for cls in post_classes:
        elements = soup.find_all(class_=lambda x: x and cls in " ".join(x).lower())
        if elements:
            print(f"   📝 Found {len(elements)} elements with '{cls}' in class")
            for i, elem in enumerate(elements[:2], 1):
                title = _extract_text_sample(elem)
                print(f"     {i}. {title[:60]}...")

    # Check for headings with links
    headings_with_links = []
    for tag in ["h1", "h2", "h3", "h4"]:
        headings = soup.find_all(tag)
        for h in headings:
            if h.find("a"):
                headings_with_links.append(h)

    if headings_with_links:
        print(f"   🔗 Found {len(headings_with_links)} headings with links")
        for i, h in enumerate(headings_with_links[:3], 1):
            title = _extract_text_sample(h)
            print(f"     {i}. <{h.name}> {title[:50]}...")


def _suggest_manual_selectors(soup, url: str) -> None:
    """Suggest manual selectors based on page structure."""
    suggestions = []

    # Look for title patterns
    title_elements = soup.find_all(["h1", "h2", "h3", "h4"])
    for elem in title_elements:
        if elem.find("a"):  # Has a link
            classes = elem.get("class", [])
            if classes:
                suggestions.append(f"h{elem.name[1]} .{classes[0]}")
            else:
                suggestions.append(f"h{elem.name[1]} a")

    # Look for common patterns
    for selector in ["article", "section", ".post", ".entry", ".blog-post"]:
        elements = soup.select(selector)
        if 1 <= len(elements) <= 10:
            suggestions.append(selector)

    if suggestions:
        print("   Suggested selectors to try:")
        for sugg in suggestions[:5]:
            print(f"     • {sugg}")
    else:
        print("   No obvious selectors found - manual inspection needed")


def _extract_text_sample(element) -> str:
    """Extract a text sample from an element."""
    if not element:
        return ""

    # Try to get meaningful text
    text = element.get_text().strip()
    if len(text) > 20:
        return text

    # If too short, try child elements
    for child in element.find_all(["h1", "h2", "h3", "h4", "a"]):
        child_text = child.get_text().strip()
        if len(child_text) > 10:
            return child_text

    return text


def analyze_failed_blogs() -> None:
    """Analyze all blogs that fell back to page titles."""

    # Load current blog states
    states_file = Path("blog_states.json")
    if not states_file.exists():
        print("❌ No blog states found. Run initialization first.")
        return

    with open(states_file, "r") as f:
        states = json.load(f)

    # Find fallback blogs
    fallback_blogs = []
    for blog_name, state in states.items():
        if state.get("last_post_title", "").startswith("Fallback -"):
            fallback_blogs.append((blog_name, state.get("last_post_url", "")))

    if not fallback_blogs:
        print("✅ No blogs need manual tuning!")
        return

    print(f"🔧 Found {len(fallback_blogs)} blogs that need manual tuning:")
    for blog_name, url in fallback_blogs:
        print(f"   • {blog_name}")

    print(f"\n{'=' * 60}")
    print("DETAILED ANALYSIS")
    print(f"{'=' * 60}")

    for blog_name, url in fallback_blogs:
        analyze_blog_structure(url, blog_name)
        input("\nPress Enter to continue to next blog...")


def test_manual_selector(url: str, selector: str) -> None:
    """
    Test a manual selector on a blog.

    Args:
        url: The blog URL
        selector: The CSS selector to test
    """
    print(f"\n🧪 TESTING SELECTOR: {selector}")
    print(f"URL: {url}")

    with WebScraper() as scraper:
        soup = scraper.fetch_and_parse(url)
        if not soup:
            print("❌ Failed to fetch page")
            return

        # Test the selector
        elements = soup.select(selector)
        print("\n📊 RESULTS:")
        print(f"Found {len(elements)} elements")

        if not elements:
            print("❌ No elements found with this selector")
            return

        # Show found elements
        for i, elem in enumerate(elements[:5], 1):
            title = _extract_text_sample(elem)
            links = elem.find_all("a", href=True)
            link_text = f" -> {links[0].get('href')}" if links else ""
            print(f"   {i}. {title[:60]}...{link_text}")

        if len(elements) > 5:
            print(f"   ... and {len(elements) - 5} more")


if __name__ == "__main__":
    analyze_failed_blogs()
