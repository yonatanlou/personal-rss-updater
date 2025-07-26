# Personal RSS Updater

[![Python](httpshttps://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![GitHub Actions](https://github.com/yonatanlou/personal-rss-updater/workflows/Daily%20RSS%20Check/badge.svg)](https://github.com/yonatanlou/personal-rss-updater/actions)

A robust Python program that monitors blogs for new posts and sends daily email digest notifications. It uses intelligent web scraping to support both RSS and non-RSS blogs.

## Features

- Universal blog monitoring (RSS and non-RSS)
- Intelligent, automatic post detection
- Dual monitoring modes (scrape/feed) for flexible handling
- Daily email digests (HTML & text)
- Failure tracking and bi-weekly reminders for problematic blogs
- Modern Python setup using `uv`

## Setup and Quick Start

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Configure:**
    - Copy and edit the configuration file: `cp config.yaml.example config.yaml`
    - Set environment variables for your email credentials:
      ```bash
      export EMAIL_USERNAME="your-email@gmail.com"
      export EMAIL_PASSWORD="your-app-password" 
      # Use a Google App Password: https://support.google.com/accounts/answer/185833
      ```

3.  **Initialize:**
    This command marks all current posts as "read."
    ```bash
    uv run python -m rss_updater.main init
    ```

4.  **Run Monitoring:**
    ```bash
    uv run python -m rss_updater.main
    ```

## Configuration

### `config.yaml`

- `email`: SMTP server, port, and recipient.
- `retry_count`: Retries for failed requests.
- `failure_threshold`: Number of failures before a blog is marked as problematic.

### `blogs.json`

List the blogs you want to monitor. The `monitoring_strategy` field is key:
- `"scrape"` (default): The tool will actively scrape the site to find new posts.
- `"feed"`: The tool will not scrape the site. Instead, it will send you a reminder every two weeks to check the blog manually. This is useful for blogs that are difficult to scrape or update infrequently.

```json
[
  {
    "name": "Example Blog (Scrape)",
    "url": "https://example.com/blog",
    "monitoring_strategy": "scrape"
  },
  {
    "name": "Gwern.net Newsletter (Feed)",
    "url": "https://gwern.net/changelog",
    "monitoring_strategy": "feed"
  }
]
```

### `manual_selectors.json` (Optional)

For blogs where automatic detection fails, you can specify manual CSS selectors.

## Usage

```bash
# Run the main monitoring loop
uv run python -m rss_updater.main

# Initialize blog states (run once at setup)
uv run python -m rss_updater.main init

# Send a test email to verify setup
uv run python -m rss_updater.main test-email

# Analyze a blog's structure for debugging
uv run python -m rss_updater.main analyze --url https://example.com
```

## GitHub Actions for Automation

This repository includes a GitHub Actions workflow to run the monitor daily.

1.  **Add Repository Secrets:**
    In your GitHub repository, go to `Settings > Secrets and variables > Actions` and add:
    - `EMAIL_USERNAME`: Your email address.
    - `EMAIL_PASSWORD`: Your email app password.

2.  **Run Initialization Workflow:**
    The first time, you need to manually run the "Initialize RSS States" workflow from the Actions tab on GitHub. This will create and commit the initial `blog_states.json`.

The `daily-rss-check.yml` workflow will then run automatically every day, check for new posts, and commit the updated state file.

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format and lint
uv run black .
uv run ruff check .
```

## License

[MIT](https://opensource.org/licenses/MIT)