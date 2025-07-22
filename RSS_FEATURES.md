# RSS/Atom Feed Support

This document describes the new RSS/Atom feed functionality implemented in the Personal RSS Updater.

## Features Implemented

### 1. RSS/Atom Feed Auto-Detection

The system can automatically detect RSS and Atom feeds from websites using multiple methods:

- **HTML Link Tags**: Scans `<link rel="alternate">` tags in HTML head
- **Common Feed Paths**: Checks standard feed endpoints like `/feed`, `/rss.xml`, `/atom.xml`, etc.
- **Content-based Detection**: Looks for feed-like links in page content

**Usage:**
```bash
rss-updater detect-feeds --url https://example.com
```

### 2. RSS/Atom Feed Parser

Supports parsing of multiple feed formats:

- RSS 1.0, RSS 2.0
- Atom feeds
- Handles malformed feeds gracefully
- Extracts title, link, description, publication date, author

**Features:**
- HTTP caching support (ETag, Last-Modified)
- Conditional requests to minimize bandwidth
- HTML content cleaning and text extraction

### 3. Feed Validation and Health Checks

Comprehensive feed validation system:

- Connectivity testing
- Content validation
- Performance metrics
- Quality assessment
- Caching header analysis

**Usage:**
```bash
rss-updater validate-feed --url https://example.com/feed.xml
```

### 4. Hybrid Monitoring Mode

The new hybrid approach tries RSS feeds first, then falls back to web scraping:

1. **RSS First**: Attempts to use RSS/Atom feeds for faster, more reliable monitoring
2. **Web Scraping Fallback**: Falls back to traditional web scraping if RSS fails
3. **Feed Caching**: Caches discovered feed URLs for future use
4. **Performance Tracking**: Reports which method was used for each blog

**Usage:**
```bash
# Use hybrid mode for monitoring
rss-updater hybrid-check

# Use hybrid mode with regular run command
rss-updater run --use-hybrid
```

## Benefits of RSS Support

### 1. Reliability
- RSS feeds are structured and less prone to breaking when websites change
- Standardized format means consistent parsing
- Built-in metadata like publication dates

### 2. Performance
- Faster parsing compared to HTML scraping
- HTTP caching reduces bandwidth usage
- Less server load on target websites

### 3. Accuracy
- Direct access to post metadata
- No need for heuristic content detection
- Consistent post identification

### 4. Respectful
- Lower server impact
- Follows web standards
- Respects caching headers

## Technical Implementation

### Architecture

```
feeds/
├── __init__.py
├── detector.py      # RSS/Atom feed discovery
├── parser.py        # Feed parsing with feedparser
├── validator.py     # Feed health checking
├── hybrid_monitor.py # Combined RSS + scraping monitor
└── models.py        # Feed data models
```

### Key Classes

- **FeedDetector**: Discovers RSS/Atom feeds from websites
- **FeedParser**: Parses RSS/Atom feeds into structured data
- **FeedValidator**: Validates and health-checks feeds
- **HybridBlogMonitor**: Combines RSS and web scraping approaches
- **Feed/FeedEntry**: Data models for feed content

### Dependencies

- `feedparser>=6.0.0`: Industry-standard RSS/Atom parsing library
- Existing dependencies: `requests`, `beautifulsoup4`, etc.

## CLI Commands

### Feed Detection
```bash
rss-updater detect-feeds --url <website-url>
```
Discovers all RSS/Atom feeds for a website and recommends the best one.

### Feed Validation
```bash
rss-updater validate-feed --url <feed-url>
```
Validates a specific RSS/Atom feed and provides health metrics.

### Hybrid Monitoring
```bash
rss-updater hybrid-check
```
Runs monitoring using the hybrid approach (RSS + web scraping fallback).

### Regular Run with Hybrid Mode
```bash
rss-updater run --use-hybrid
```
Uses hybrid monitoring in the regular run workflow.

## Storage Extensions

The blog state storage has been extended to support RSS-specific fields:

- `feed_url`: Cached RSS feed URL for the blog
- `feed_etag`: ETag header for conditional requests
- `feed_modified`: Last-Modified datetime for caching
- `last_post_date`: Publication date of the last post (for RSS comparison)

## Migration Path

The hybrid system is designed for seamless migration:

1. **Backward Compatible**: Existing configurations continue to work
2. **Gradual Adoption**: Can be enabled per-command or with flags
3. **Fallback Safety**: Web scraping remains as backup method
4. **Feed Discovery**: Automatically discovers and caches RSS feeds

## Testing

Comprehensive test suite covers:

- Feed detection algorithms
- Feed parsing with various formats
- Feed validation and health checking
- Error handling and edge cases
- Data model validation

**Run tests:**
```bash
uv run python -m pytest tests/test_feeds.py -v
```

## Future Enhancements

1. **Feed Categorization**: Organize feeds by content type
2. **Feed Analytics**: Track feed health over time
3. **Feed Prioritization**: Smart feed selection based on quality metrics
4. **OPML Import/Export**: Standard feed list management
5. **Feed Aggregation**: Combine multiple feeds for a single source
