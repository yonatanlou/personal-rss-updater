# Personal RSS Updater

A robust Python program that monitors blogs for new posts and sends daily email digest notifications. Uses intelligent web scraping to support both RSS and non-RSS blogs.

## Features

- **Universal blog monitoring** - Supports both RSS feeds and regular websites
- **Intelligent selector detection** - Automatically detects blog post structures
- **Manual selector overrides** - Configure custom selectors for problematic blogs
- **Daily email digest** - Beautiful HTML and plain text notifications
- **Failure tracking** - Monitors blog health and sends alerts for persistent issues
- **Bi-weekly reminders** - Notifications for blogs needing attention
- **Modern Python setup** - Uses uv for dependency management
- **Modular architecture** - Clean, organized codebase with proper separation of concerns

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Quick Start

1. **Set up configuration:**
   ```bash
   # Copy example config and customize
   cp config.yaml.example config.yaml
   ```

2. **Set environment variables:**
   ```bash
   export EMAIL_USERNAME="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password" 
   ```
app password: https://support.google.com/accounts/answer/185833?hl=en
3. **Initialize blog states:**
   ```bash
   uv run python -m rss_updater.main init
   ```

4. **Test email configuration:**
   ```bash
   uv run python -m rss_updater.main test-email
   ```

5. **Run monitoring:**
   ```bash
   uv run python -m rss_updater.main
   ```

## Configuration

### config.yaml

```yaml
email:
  smtp_server: smtp.gmail.com    # SMTP server
  smtp_port: 587                 # SMTP port
  recipient: your@email.com      # Email recipient

retry_count: 3                   # Number of retries for failed requests
failure_threshold: 3             # Failures before marking blog as problematic
user_agent: "Mozilla/5.0 (Personal RSS Updater)"  # User agent string
request_delay: 1.0              # Delay between requests (seconds)
```

### blogs.json

Add blogs to monitor in `blogs.json`:

```json
[
  {
    "name": "Blog Name",
    "url": "https://example.com/blog/",
    "description": "Optional description"
  }
]
```



### Manual Selectors (manual_selectors.json)

For blogs that automatic detection can't handle:

```json
{
  "example.com": {
    "post_container": ".post-item",
    "title_selector": "h2.title",
    "link_selector": "a.permalink"
  }
}
```

## Commands

### Core Commands

```bash
# Run main monitoring loop
uv run python -m rss_updater.main

# Initialize blog states (mark current posts as read)
uv run python -m rss_updater.main init

# Sync blog states with blogs.json configuration
uv run python -m rss_updater.main sync

# Check blogs without sending email
uv run python -m rss_updater.main check

# Send test email
uv run python -m rss_updater.main test-email
```

### Analysis Commands

```bash
# Analyze failed blogs
uv run python -m rss_updater.main analyze

# Analyze specific blog structure
uv run python -m rss_updater.main analyze --url https://example.com --blog-name "Example Blog"

# Test manual selector
uv run python -m rss_updater.main test-selector --url https://example.com --selector ".post-item"
```

### Command Options

- `--mark-as-read` - Mark current posts as already read during init (default: true)
- `--url` - Specify URL for analysis commands
- `--selector` - CSS selector to test
- `--blog-name` - Blog name for analysis

## Project Structure

```
src/rss_updater/
├── core/           # Core functionality (config, models)
├── detection/      # Blog post detection logic
├── monitoring/     # Blog monitoring and diagnostics  
├── notification/   # Email notification system
├── storage/        # Data persistence layer
├── utils/          # Utility functions
├── web/           # Web scraping functionality
├── main.py        # Main entry point
└── initializer.py # Blog initialization
```

## Development

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## How It Works

1. **Blog Discovery**: Reads blog list from `blogs.json`
2. **Intelligent Detection**: Automatically detects blog post selectors using:
   - Common CSS patterns (`.post`, `.entry`, `.article`)
   - Structural analysis (repeated elements)
   - Link analysis (internal links with content)
3. **Manual Overrides**: Falls back to manual selectors when automatic detection fails
4. **State Tracking**: Maintains persistent state in `blog_states.json`
5. **Change Detection**: Compares current posts with stored state
6. **Email Notifications**: Sends digest emails for new posts and failure alerts

## Troubleshooting

### Common Issues

1. **Email not sending**: Check EMAIL_USERNAME and EMAIL_PASSWORD environment variables
2. **Blog not detected**: Add manual selectors to `manual_selectors.json`
3. **Import errors**: Run `uv sync` to install dependencies

### Debug Commands

```bash
# Analyze specific blog
uv run python -m rss_updater.main analyze --url https://problematic-blog.com

# Test email configuration
uv run python -m rss_updater.main test-email

# Check storage state
cat blog_states.json | jq .
```

## License

MIT License
