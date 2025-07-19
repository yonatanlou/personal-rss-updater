# Personal RSS Updater

A robust Python program that monitors blogs for new posts and sends daily email digest notifications. Uses intelligent web scraping to support both RSS and non-RSS blogs.

## Features

- Universal blog monitoring (RSS and non-RSS blogs)
- Intelligent selector detection for automatic blog structure analysis
- Daily email digest notifications
- Modern Python setup with uv dependency management
- Flexible deployment (local and GitHub Actions)

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Usage

```bash
# Run the application
uv run python -m rss_updater.main

# Or use the installed script
rss-updater
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

## Configuration

Configuration is managed through YAML files and environment variables for sensitive data.

## License

MIT License
