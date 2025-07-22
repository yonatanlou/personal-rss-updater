# RSS Updater - Feature Roadmap & TODO

## 🚀 High Priority Features

### 1. Native RSS/Atom Feed Support
- [ ] **Auto-detect RSS feeds** on websites
  - Scan for `<link rel="alternate">` tags in HTML head
  - Check common RSS endpoints (`/feed`, `/rss`, `/atom.xml`, etc.)
  - Prefer RSS feeds over web scraping when available
  - parse also a feed xml in sites, like in https://koaning.io/feed.xml or https://harper.blog/index.xml
- [ ] **RSS/Atom parser** implementation
  - Support RSS 1.0, RSS 2.0, and Atom formats
  - Extract title, link, description, publication date
  - Handle malformed feeds gracefully
- [ ] **Feed validation** and health checks
  - Detect moved/redirected feeds
  - Handle HTTP caching headers (ETag, Last-Modified)
  - Validate feed structure and content
- [ ] **Hybrid mode** - RSS + fallback to scraping
  - Try RSS first, fall back to web scraping if RSS fails
  - Compare RSS and scraped content for accuracy

### 2. Blog Import/Export System
- [ ] **OPML import** (standard RSS format)
  - Parse OPML files from popular RSS readers
  - Extract blog name, URL, categories
  - Batch import with validation
- [ ] **CSV import** functionality
  - Support custom CSV formats: `name,url,category,description`
  - Data validation and duplicate detection
  - Preview before import
- [ ] **Export capabilities**
  - Export current blogs to OPML format
  - Export to CSV with statistics
  - Backup blog states and configurations
- [ ] **Migration tools** from popular RSS readers
  - Feedly OPML import
  - Inoreader backup import
  - Google Reader-style imports

### 3. Enhanced Web Interface
- [ ] **Simple web dashboard** for blog management
  - Add/remove/edit blogs
  - View recent posts and statistics
  - Manage manual selectors
  - Test blog configurations
- [ ] **Configuration management** via web UI
  - Edit email settings
  - Adjust monitoring frequencies
  - Manage notification preferences
- [ ] **Real-time monitoring** dashboard
  - Live feed status updates
  - Recent post previews
  - Error logs and diagnostics

## 📈 Medium Priority Features

### 4. Advanced Content Management
- [ ] **Blog categorization** and tagging
  - Organize blogs by topics (Tech, News, Personal, etc.)
  - Filter emails by categories
  - Category-specific notification settings
- [ ] **Content filtering** options
  - Keyword inclusion/exclusion filters
  - Title/content length filters
  - Language detection and filtering




### 5. Performance & Reliability
- [ ] **Intelligent rate limiting**
  - Adaptive delays based on server response
  - Respect robots.txt and crawl-delay
  - Distributed load across time windows
- [ ] **Caching improvements**
  - Cache parsed content and selectors
  - ETags and conditional requests
  - Intelligent cache invalidation
- [ ] **Retry logic enhancement**
  - Exponential backoff with jitter
  - Circuit breaker pattern for failing blogs
  - Temporary vs permanent failure detection

## 🔧 Technical Improvements

### 6. Code Quality & Development Tools
- [ ] **Fix linting and type checking issues**
  - Resolve Ruff linting errors in codebase
  - Fix MyPy type annotation issues
  - Add proper type hints to all functions
  - Clean up unused variables and imports
- [ ] **Enhanced pre-commit hooks**
  - Re-enable Black, Ruff, and MyPy in pre-commit after fixes
  - Add more comprehensive code quality checks
  - Configure proper type checking strictness

### 7. Architecture & Infrastructure
- [ ] **Database backend** (optional SQLite/PostgreSQL)
  - Replace JSON storage for better performance
  - Support for complex queries and reporting
  - Data migration tools
- [ ] **Docker containerization**
  - Multi-stage builds for production
  - Docker Compose for local development
  - Kubernetes deployment manifests
- [ ] **API endpoints** for external integration
  - REST API for blog management
  - Webhook endpoints for external triggers
  - API authentication and rate limiting



### 8. Advanced Content Processing
- [ ] **Content summarization** (AI-powered)
  - Generate brief summaries of long posts
  - Extract key points and highlights
  - Support for multiple languages
- [ ] **Duplicate detection** and deduplication
  - Identify cross-posted content
  - Merge similar posts from different sources
  - Content similarity algorithms
- [ ] **Content enrichment**
  - Auto-categorization using ML
  - Sentiment analysis of posts
  - Extract and highlight key topics


## 🛠️ Implementation Notes

### Development Priorities
1. **Start with RSS support** - Most impactful for existing users
2. **Add import/export** - Essential for user onboarding
3. **Build web interface** - Improves usability significantly
4. **Focus on reliability** - Core functionality must be rock-solid

### Technical Considerations
- **Maintain backward compatibility** with existing configurations
- **Progressive enhancement** - new features shouldn't break existing setups
- **Performance first** - don't sacrifice speed for features
- **Security** - especially important for web interface and API features

### Testing Strategy
- **Unit tests** for all new core functionality
- **Integration tests** for RSS parsing and web scraping
- **End-to-end tests** for critical user workflows
- **Performance benchmarks** for scalability features

---

*This roadmap is living document - priorities may shift based on user feedback and technical constraints.*
