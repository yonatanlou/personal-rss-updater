# RSS Updater System Context & Debugging Guide

This document provides comprehensive context for debugging and fixing scraping issues in the RSS Updater system. Use this as your primary reference when a blog scraper stops working.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Critical Files & Structure](#critical-files--structure)
- [Debugging Workflow](#debugging-workflow)
- [Common Scraping Issues](#common-scraping-issues)
- [Manual Selector Configuration](#manual-selector-configuration)
- [Testing & Verification](#testing--verification)
- [Known Working Examples](#known-working-examples)

## 🏗️ System Overview

The RSS Updater is a blog monitoring system that:
1. **Monitors blogs** for new posts using web scraping or RSS feeds
2. **Detects changes** by comparing current posts with stored state
3. **Sends notifications** via email when new posts are found
4. **Prevents duplicates** by only updating storage after successful email delivery

### Architecture Flow
```
Blog Check → Detection → New Post Found → Email Sent → Storage Updated
     ↓            ↓            ↓              ↓            ↓
  WebScraper → Detector → BlogMonitor → EmailNotifier → BlogStorage
```

## 📁 Critical Files & Structure

### Configuration Files
- **`config/app/blogs.json`** - Blog list and monitoring strategies
- **`config/app/manual_selectors.json`** - Manual CSS selectors for problematic blogs
- **`data/blog_states.json`** - Persistent state tracking for each blog

### Core Detection System
- **`src/rss_updater/detection/detector.py`** - Main detection orchestrator
- **`src/rss_updater/detection/post_extractor.py`** - Extracts titles/URLs from HTML
- **`src/rss_updater/detection/pattern_detector.py`** - Automatic pattern detection
- **`src/rss_updater/detection/content_analyzer.py`** - Content analysis for post detection

### Monitoring & Storage
- **`src/rss_updater/monitoring/monitor.py`** - Main blog monitoring logic
- **`src/rss_updater/storage/blog_storage.py`** - Persistent state management
- **`src/rss_updater/web/scraper.py`** - Web scraping utilities

### Email & Notifications
- **`src/rss_updater/notification/emailer.py`** - Email sending logic
- **`src/rss_updater/cli/commands.py`** - CLI orchestration and email triggering

## 🔍 Debugging Workflow

### Step 1: Identify the Problem

**Check the blog state first:**
```bash
# Look at what the system currently thinks is the latest post
grep -A 10 "BLOG_NAME" data/blog_states.json
```

**Common problematic patterns:**
- `"last_post_title": "BLOG_NAME"` (detecting site title instead of post)
- `"last_post_title": "Fallback - ..."` (detection completely failed)
- `"last_post_url": "https://site.com/"` (detecting homepage instead of post URL)

### Step 2: Manual Investigation

**Fetch the blog page and analyze structure:**
```python
# Use this Python script template
from src.rss_updater.web.scraper import WebScraper
from src.rss_updater.detection.detector import SelectorDetector

with WebScraper(user_agent='Mozilla/5.0 (compatible; RSS-Updater)') as scraper:
    soup = scraper.fetch_and_parse('BLOG_URL')
    if soup:
        detector = SelectorDetector()
        result = detector.get_latest_post(soup, 'BLOG_URL', 'BLOG_NAME')
        print(f'Current detection: {result}')
```

### Step 3: Analyze What Should Be Detected

**Use WebFetch to understand the blog structure:**
```
Find the latest 3-5 blog posts on the homepage.
What HTML elements contain the blog posts?
How are post titles and links structured?
What CSS selectors would work best?
```

### Step 4: Test Manual Selectors

**Try different selector approaches:**
```python
# Test potential selectors directly
containers = soup.select("POTENTIAL_SELECTOR")
for i, container in enumerate(containers[:3]):
    print(f"{i+1}. {container.get_text().strip()}")
    if container.name == 'a':
        print(f"   URL: {container.get('href')}")
```

### Step 5: Create Manual Selector

Add to `config/app/manual_selectors.json`:
```json
{
  "BLOG_NAME": {
    "post_container": "CSS_SELECTOR_FOR_POST_ELEMENTS",
    "title_selector": "CSS_SELECTOR_FOR_TITLE_WITHIN_CONTAINER", 
    "link_selector": "CSS_SELECTOR_FOR_LINK_WITHIN_CONTAINER",
    "description": "Brief description of the blog structure"
  }
}
```

### Step 6: Test and Verify

**Test the manual selector:**
```python
# Verify the manual selector works
detector = SelectorDetector()
result = detector.get_latest_post(soup, 'BLOG_URL', 'BLOG_NAME')
print(f'With manual selector: {result}')
```

## 🚨 Common Scraping Issues

### Issue 1: Detecting Site Title Instead of Post Title

**Symptoms:**
- `last_post_title` matches the blog name or site title
- `last_post_url` is the homepage URL

**Debugging:**
```python
# Check what the automatic detector is finding
print("H1 elements:", [h1.get_text().strip() for h1 in soup.find_all('h1')])
print("Title tag:", soup.title.get_text().strip() if soup.title else "None")
```

**Fix:** Usually needs a manual selector targeting the actual post elements.

### Issue 2: Picking Up Navigation or Section Headers

**Symptoms:**
- `last_post_title` is something like "Recent Posts", "Blog", "Latest", etc.
- URL might be a fragment link (`#section`) or category page

**Debugging:**
```python
# Look for actual blog post links
blog_links = soup.find_all('a', href=lambda x: x and ('blog' in x or 'post' in x))
for link in blog_links[:5]:
    print(f"Link: {link.get_text().strip()} -> {link.get('href')}")
```

**Fix:** Create manual selector targeting actual post links, often with `href` filters.

### Issue 3: RSS Feed vs Scraping Conflicts

**Symptoms:**
- Blog has `monitoring_strategy: "feed"` but still being scraped
- Or should use RSS but is set to scrape

**Check:**
```bash
# Look at blogs.json configuration
grep -A 5 -B 5 "BLOG_NAME" config/app/blogs.json
```

**Fix:** Update `monitoring_strategy` in `blogs.json` to either `"feed"` or `"scrape"`.

### Issue 4: Dynamic Content / JavaScript Required

**Symptoms:**
- Page loads but post elements are not found
- Blog uses client-side rendering

**Debugging:**
```python
# Check if basic content loads
print("Page title:", soup.title.get_text() if soup.title else "None")
print("Body length:", len(soup.body.get_text()) if soup.body else 0)
print("Script tags:", len(soup.find_all('script')))
```

**Fix:** Often requires switching to RSS feed monitoring if available.

## ⚙️ Manual Selector Configuration

### Standard Patterns

**Most blogs follow one of these patterns:**

#### Pattern 1: Post Links in a List
```json
{
  "post_container": "article",
  "title_selector": "h2 a",
  "link_selector": "h2 a"
}
```

#### Pattern 2: Direct Blog Links
```json
{
  "post_container": "a[href*='/blog/']",
  "title_selector": "self",
  "link_selector": "self"
}
```

#### Pattern 3: Post Containers with Nested Elements
```json
{
  "post_container": ".post",
  "title_selector": ".post-title",
  "link_selector": ".post-title a"
}
```

### Special Selector Values

- **`"self"`** - Use the container element itself (for when container IS the title/link)
- **`""`** - Empty string to skip that extraction step

### CSS Selector Tips

**Common selectors:**
- `a[href^='/blog/']` - Links starting with `/blog/`
- `a[href*='/post/']` - Links containing `/post/`
- `h2 a, h3 a` - Links within headings
- `.post-title a` - Links within post title classes
- `article h2` - H2 headings within article elements

**Attribute selectors:**
- `[href*='blog']:not([href*='index'])` - Contains 'blog' but not 'index'
- `a[href]:not([href^='#'])` - Links that aren't just fragments
- `a[href^='http']` - Only absolute URLs

## 🧪 Testing & Verification

### Quick Manual Test
```bash
# Test a specific blog's detection
uv run python -c "
from src.rss_updater.web.scraper import WebScraper
from src.rss_updater.detection.detector import SelectorDetector

with WebScraper() as scraper:
    soup = scraper.fetch_and_parse('BLOG_URL')
    detector = SelectorDetector()
    result = detector.get_latest_post(soup, 'BLOG_URL', 'BLOG_NAME')
    print(f'Result: {result}')
"
```

### Full System Test
```bash
# Run monitoring for a single blog (if possible)
uv run python -m rss_updater monitor --blog "BLOG_NAME"
```

### Check Blog State After Fix
```bash
# Verify the state was updated correctly
grep -A 10 "BLOG_NAME" data/blog_states.json
```

## 📚 Known Working Examples

### Julia Evans (Direct Blog Links)
```json
{
  "Julia Evans": {
    "post_container": "a[href^='/blog/']",
    "title_selector": "self",
    "link_selector": "self",
    "description": "Posts are direct links starting with /blog/"
  }
}
```

### Nicholas Carlini (Class-based Structure)
```json
{
  "Nicholas Carlini": {
    "post_container": ".post",
    "title_selector": "h3",
    "link_selector": "h3 a",
    "description": "Research blog with h3 titles"
  }
}
```

### Gwern.net (Complex URL Filtering)
```json
{
  "Gwern.net Newsletter": {
    "post_container": "div",
    "title_selector": "a",
    "link_selector": "a[href*='/blog/']:not([href*='index'])",
    "description": "Blog post links excluding index/navigation"
  }
}
```

## 🚀 Quick Fix Checklist

When a blog stops working:

1. **✅ Check blog state** - What is currently detected?
2. **✅ Fetch blog page** - Does the structure still exist?
3. **✅ Identify actual posts** - What should be detected?
4. **✅ Test manual selectors** - Find working CSS selectors
5. **✅ Add to manual_selectors.json** - Create configuration
6. **✅ Verify fix** - Test the detection works
7. **✅ Check email flow** - Ensure notifications work

## 🔧 Advanced Debugging

### Enable Debug Output
```python
# Add to detection code for more verbose output
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect HTML Structure
```python
# Save HTML for manual inspection
with open('debug.html', 'w') as f:
    f.write(str(soup))
```

### Test Different User Agents
```python
# Some sites block certain user agents
scraper = WebScraper(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
```

---

**Remember:** The key to fixing scraping issues is understanding the HTML structure of each blog and creating targeted CSS selectors that reliably find the latest post title and URL.