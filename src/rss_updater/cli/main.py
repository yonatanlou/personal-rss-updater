"""Main CLI entry point."""

import sys
import argparse
from typing import NoReturn
from dotenv import load_dotenv

from .commands import CommandHandler


def main() -> NoReturn:
    """Main entry point for the RSS updater application."""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="Personal RSS Updater")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=[
            "run",
            "init",
            "sync",
            "analyze",
            "test-selector",
            "check",
            "test-email",
            "detect-feeds",
            "validate-feed",
            "hybrid-check",
        ],
        help="Command to execute (default: run)",
    )
    parser.add_argument(
        "--mark-as-read",
        action="store_true",
        default=True,
        help="Mark current posts as already read during init",
    )
    parser.add_argument("--url", help="URL to analyze or test (for analyze/test-selector commands)")
    parser.add_argument("--selector", help="CSS selector to test (for test-selector command)")
    parser.add_argument("--blog-name", help="Blog name for analysis")
    parser.add_argument(
        "--use-hybrid",
        action="store_true",
        default=False,
        help="Use hybrid mode (RSS + scraping fallback) for run command",
    )

    args = parser.parse_args()

    print("RSS Updater starting...")
    print("Personal RSS Updater v0.1.0")
    print("Monitoring blogs for new posts and sending daily digest notifications")

    # Initialize command handler
    handler = CommandHandler(args)

    # Route to appropriate command handler
    command_map = {
        "init": handler.handle_init,
        "sync": handler.handle_sync,
        "analyze": handler.handle_analyze,
        "test-selector": handler.handle_test_selector,
        "check": handler.handle_check,
        "test-email": handler.handle_test_email,
        "detect-feeds": handler.handle_detect_feeds,
        "validate-feed": handler.handle_validate_feed,
        "hybrid-check": handler.handle_hybrid_check,
        "run": handler.handle_run,
    }

    if args.command in command_map:
        command_map[args.command]()
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    print("RSS Updater finished.")
    sys.exit(0)


if __name__ == "__main__":
    main()
