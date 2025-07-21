# Personal RSS Updater - System Context

## Overview
A Python-based blog monitoring system that automatically detects new posts across multiple blogs and sends daily email digests. Supports both RSS feeds and intelligent web scraping for non-RSS sites.

## Core Purpose
- Monitor blog lists for new content
- Send daily email notifications with new posts
- Handle blog failures with alerts and retry logic
- Support both RSS and non-RSS blogs through intelligent detection

## Architecture

### Core Components
- **Detection Engine** (`src/rss_updater/detection/`) - Analyzes blog structures and extracts posts
- **Storage Layer** (`src/rss_updater/storage/`) - Manages blog states and post history
- **Notification System** (`src/rss_updater/notification/`) - Generates and sends email digests
- **Monitoring** (`src/rss_updater/monitoring/`) - Tracks blog health and diagnostics
- **Web Scraping** (`src/rss_updater/web/`) - Handles HTTP requests and content extraction

### Key Data Models
- **Post** - Represents individual blog posts with title, URL, date, excerpt
- **Blog** - Blog configuration with URL, selectors, and state
- **BlogState** - Tracks post history, failures, and health per blog

### Configuration Files
- `config.yaml` - Email settings, retry logic, user agent configuration
- `blogs.json` - List of blogs to monitor with URLs and descriptions
- `manual_selectors.json` - Custom CSS selectors for problematic blogs
- `blog_states.json` - Persistent state tracking (auto-generated)

## Data Flow

1. **Initialization** - Load blog list and initialize states if needed
2. **Detection Loop**:
   - For each blog: scrape content using automatic or manual selectors
   - Extract posts using intelligent pattern detection
   - Compare with stored state to identify new posts
3. **Notification** - Generate HTML/text email digest for new posts
4. **State Update** - Persist updated blog states and post history
5. **Error Handling** - Track failures and send alerts for persistent issues

## Key Features

### Intelligent Detection
- Automatic CSS selector discovery using common patterns
- Fallback to manual selectors when needed
- Link validation and content analysis
- Structural pattern recognition for post containers

### State Management
- JSON-based persistence for blog states
- Post history tracking to prevent duplicates  
- Failure counting with configurable thresholds
- Sync operations to maintain data consistency

### Email System
- HTML and plain text digest generation
- SMTP configuration with Gmail app password support
- Failure alerts and bi-weekly reminders
- Configurable recipients and formatting

### GitHub Actions Integration
- Daily automated runs with cron scheduling
- State persistence through git commits
- Auto-initialization if states don't exist
- Manual workflow triggers for setup

## Technology Stack
- **Python 3.10+** with modern async/await patterns
- **uv** for dependency management and virtual environments
- **BeautifulSoup4 + lxml** for HTML parsing and CSS selection
- **Requests** for HTTP client functionality
- **Pydantic** for data validation and settings
- **PyYAML** for configuration management

## Common Operations

### Development
```bash
uv sync              # Install dependencies
uv run python -m rss_updater.main init  # Initialize blog states
uv run python -m rss_updater.main       # Run monitoring
uv run pytest       # Run tests
```

### Analysis & Debugging
```bash
uv run python -m rss_updater.main analyze                    # Analyze failed blogs
uv run python -m rss_updater.main analyze --url <URL>       # Analyze specific blog
uv run python -m rss_updater.main test-selector --selector <CSS>  # Test selectors
```

## File Structure Patterns
- **Core Logic**: `src/rss_updater/core/` - Models, config, shared utilities
- **Feature Modules**: Each major feature has its own directory with `__init__.py`
- **Storage**: JSON files for configuration and state persistence
- **Tests**: `tests/` directory with pytest-based test suite
- **Documentation**: README.md covers setup, config, and troubleshooting

## Error Handling Strategy
- Retry logic with configurable attempts and delays  
- Failure threshold tracking before marking blogs as problematic
- Email alerts for persistent failures
- Graceful degradation when individual blogs fail
- Comprehensive logging for debugging

## Security Considerations
- Environment variables for email credentials
- No hardcoded secrets in repository
- Gmail app passwords instead of account passwords
- Input validation for URLs and configuration
- Safe HTML parsing with lxml backend

## Current State vs Future Plans
**Current**: Focuses on web scraping with JSON storage and basic email notifications
**Planned**: Native RSS support, web dashboard, database backend, content categorization
See `todo.md` for detailed feature roadmap and implementation priorities.

## Integration Points
- **GitHub Actions** for automated deployment and scheduling
- **Gmail SMTP** for email delivery
- **CSS Selectors** as the primary content extraction interface
- **JSON APIs** for configuration and state management
- **Command Line** as the primary user interface

This system prioritizes reliability, simplicity, and maintainability while providing robust blog monitoring capabilities.