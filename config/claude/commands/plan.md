# Personal RSS Updater - Implementation Plan

## Overview
This document provides a step-by-step blueprint for implementing the Personal RSS Updater project. Each step builds incrementally on the previous one, ensuring safe progress with no orphaned code.

## Phase 1: Foundation Setup

### Step 1: Project Initialization
**Goal**: Set up modern Python project structure with uv

**Prompt**:
```
Initialize a new Python project called "personal-rss-updater" using modern Python best practices:

1. Create a pyproject.toml file using uv for dependency management
2. Set Python version requirement to 3.10+
3. Add initial dependencies: requests, beautifulsoup4, lxml, pydantic, pyyaml
4. Create basic project structure:
   - src/rss_updater/ (main package)
   - src/rss_updater/__init__.py
   - src/rss_updater/main.py (entry point)
   - tests/ directory
   - README.md with basic project description
   - .gitignore for Python projects

5. Add a simple CLI entry point in main.py that prints "RSS Updater starting..."
6. Test that the project can be installed and run with: uv run python -m rss_updater.main
```

### Step 2: Configuration Management
**Goal**: Create robust configuration system

**Prompt**:
```
Implement a configuration management system building on the previous step:

1. Create src/rss_updater/config.py with:
   - Pydantic models for EmailConfig, BlogConfig, and AppConfig
   - YAML configuration file loading
   - Environment variable override support for sensitive data
   - Validation for required fields

2. Create a sample config.yaml file with:
   - Email SMTP settings (with placeholders)
   - Empty blogs list
   - Default settings (retry_count: 3, failure_threshold: 3)

3. Update main.py to:
   - Load configuration on startup
   - Print loaded configuration (masking sensitive data)
   - Handle configuration validation errors gracefully

4. Add environment variable support for EMAIL_USERNAME and EMAIL_PASSWORD
5. Test configuration loading with both valid and invalid configs
```

### Step 3: Data Storage Layer
**Goal**: Implement JSON-based persistence for blog states

**Prompt**:
```
Create a data storage system building on the configuration foundation:

1. Create src/rss_updater/storage.py with:
   - BlogState dataclass to track: blog_name, url, last_post_title, last_post_url, last_check, failure_count
   - BlogStorage class with methods: load(), save(), get_blog_state(), update_blog_state()
   - JSON serialization/deserialization with proper error handling
   - Automatic backup creation before writes

2. Create src/rss_updater/models.py with:
   - Post dataclass: title, url, date, excerpt, blog_name
   - Blog dataclass: name, url, selectors (dict)
   - Consistent data models across the application

3. Update main.py to:
   - Initialize storage system
   - Load existing blog states
   - Print summary of tracked blogs and their last check times

4. Add data migration handling for future schema changes
5. Test storage operations with sample data
```

## Phase 2: Web Scraping Engine

### Step 4: Basic Web Scraper
**Goal**: Create foundation web scraping functionality

**Prompt**:
```
Implement a basic web scraping engine building on the data models:

1. Create src/rss_updater/scraper.py with:
   - WebScraper class with session management and user-agent rotation
   - fetch_page() method with timeout, retry logic, and error handling
   - parse_page() method using BeautifulSoup
   - Proper exception handling for network issues

2. Create src/rss_updater/utils.py with:
   - URL validation and normalization
   - Date parsing utilities (for various blog date formats)
   - Text cleaning functions for excerpts
   - Rate limiting decorator

3. Update main.py to:
   - Test scraper with a simple blog URL
   - Print basic page information (title, status code)
   - Handle and display scraping errors

4. Add comprehensive logging throughout scraper operations
5. Test with various blog types to ensure robustness
```

### Step 5: Intelligent Selector Detection
**Goal**: Implement automatic blog structure detection

**Prompt**:
```
Create intelligent selector detection system building on the scraper foundation:

1. Create src/rss_updater/detector.py with:
   - SelectorDetector class that analyzes page structure
   - detect_post_selectors() method that finds likely post containers
   - scoring algorithm for selector quality (uniqueness, consistency)
   - Common blog platform patterns (WordPress, Ghost, Jekyll, etc.)

2. Add detection heuristics:
   - Look for common CSS classes: .post, .entry, .article, .blog-post
   - Analyze link patterns and date patterns
   - Score selectors based on number of matches and content quality
   - Return top 3 selector candidates with confidence scores

3. Create src/rss_updater/validator.py with:
   - Interactive validation interface
   - Display detected posts for user confirmation
   - Selector editing and testing functionality
   - Save validated selectors to configuration

4. Update main.py to:
   - Add "detect" command for analyzing new blogs
   - Test detection on a sample blog
   - Display results in user-friendly format

5. Test detection accuracy with various blog platforms
```

### Step 6: Post Extraction System
**Goal**: Extract posts using detected/configured selectors

**Prompt**:
```
Implement post extraction system building on selector detection:

1. Create src/rss_updater/extractor.py with:
   - PostExtractor class that uses configured selectors
   - extract_posts() method returning list of Post objects
   - Fallback strategies when selectors fail
   - Content cleaning and normalization

2. Add extraction features:
   - Smart excerpt generation (first paragraph or meta description)
   - Date parsing with multiple format support
   - Relative URL resolution
   - Duplicate post detection

3. Create src/rss_updater/validator.py additions:
   - Test extraction with current selectors
   - Compare extracted posts with stored latest post
   - Detect when selectors are broken or outdated

4. Update main.py to:
   - Add "extract" command for testing post extraction
   - Show extracted posts in readable format
   - Handle extraction errors gracefully

5. Test extraction with blogs from the OPML file
6. Ensure extracted data matches expected Post model structure
```

## Phase 3: Core Logic Implementation

### Step 7: Change Detection System
**Goal**: Implement new post detection logic

**Prompt**:
```
Create change detection system building on post extraction:

1. Create src/rss_updater/monitor.py with:
   - BlogMonitor class that orchestrates checking for changes
   - check_blog() method that compares latest post with stored state
   - New post detection logic
   - Failure tracking and threshold management

2. Implement monitoring logic:
   - Extract latest post from blog
   - Compare with stored latest post (title and URL)
   - Update blog state with new information
   - Track consecutive failures for error reporting

3. Add monitoring features:
   - Batch processing of multiple blogs
   - Progress reporting during checks
   - Graceful handling of individual blog failures
   - Summary statistics (new posts found, blogs checked, failures)

4. Update main.py to:
   - Add "check" command for monitoring blogs
   - Display monitoring progress and results
   - Show new posts found in current run

5. Test with configured blogs to ensure accurate change detection
6. Verify storage updates happen correctly after monitoring
```

### Step 8: Email Notification System
**Goal**: Implement daily digest email functionality

**Prompt**:
```
Create email notification system building on change detection:

1. Create src/rss_updater/emailer.py with:
   - EmailNotifier class using SMTP
   - send_digest() method for daily summaries
   - HTML email template with responsive design
   - Error notification emails for persistent failures

2. Implement email features:
   - Daily digest with chronological post ordering
   - Rich HTML formatting with blog grouping
   - Fallback plain text version
   - Email sending retry logic with exponential backoff

3. Create email templates:
   - Daily digest template with post details (title, url, blog, date, excerpt)
   - Error notification template for failed blogs
   - Clean, readable design optimized for mobile

4. Update main.py to:
   - Add "email" command for testing email functionality
   - Send test digest with sample posts
   - Validate email configuration and connectivity

5. Test email delivery with various content types
6. Ensure proper handling of SMTP authentication errors
```

## Phase 4: Integration and Workflow

### Step 9: OPML Import System
**Goal**: Import existing blog subscriptions from OPML file

**Prompt**:
```
Create OPML import functionality building on all previous components:

1. Create src/rss_updater/importer.py with:
   - OPMLImporter class for parsing OPML files
   - extract_blogs() method to get blog URLs and names
   - Batch selector detection for imported blogs
   - Progress tracking for large imports

2. Implement import workflow:
   - Parse OPML XML structure safely
   - Extract blog information (title, URL)
   - Run selector detection for each blog
   - Present results for batch validation
   - Save validated configurations

3. Add import features:
   - Skip already configured blogs
   - Handle invalid or unreachable URLs
   - Batch validation interface
   - Import progress reporting and error summary

4. Update main.py to:
   - Add "import" command for OPML processing
   - Test with the existing subscriptions-2025-07-12 file
   - Display import results and validation needed

5. Test complete import workflow with real OPML file
6. Ensure all imported blogs are properly configured and stored
```

### Step 10: Complete CLI Interface
**Goal**: Finalize command-line interface with all features

**Prompt**:
```
Complete the CLI interface building on all implemented components:

1. Update src/rss_updater/main.py with:
   - Comprehensive argument parsing using argparse
   - Commands: import, detect, check, email, run (full workflow)
   - Proper error handling and user feedback
   - Logging configuration and verbosity levels

2. Implement CLI commands:
   - `import <opml_file>`: Import and configure blogs from OPML
   - `detect <url>`: Analyze blog structure and detect selectors
   - `check`: Run monitoring for all configured blogs
   - `email`: Send test email or daily digest
   - `run`: Complete workflow (check + email if new posts found)

3. Add CLI features:
   - Progress bars for long operations
   - Colored output for better readability
   - Configuration validation on startup
   - Detailed help text for each command

4. Create comprehensive error handling:
   - Network connectivity issues
   - Configuration problems
   - Storage corruption
   - Email delivery failures

5. Test all CLI commands individually and in sequence
6. Ensure proper exit codes for scripting integration
```

## Phase 5: Deployment and Automation

### Step 11: Local Scheduling Support
**Goal**: Enable local automated execution

**Prompt**:
```
Add local scheduling and automation features:

1. Create src/rss_updater/scheduler.py with:
   - Platform-specific scheduling helpers (cron, task scheduler)
   - Schedule validation and setup
   - Local daemon mode support
   - Logging configuration for automated runs

2. Add scheduling features:
   - Generate cron expression for daily 8 AM execution
   - Create systemd service file for Linux
   - Windows Task Scheduler XML template
   - macOS LaunchAgent plist template

3. Update main.py to:
   - Add "schedule" command for local automation setup
   - Add "daemon" command for continuous running
   - Proper signal handling for graceful shutdown
   - Automated log rotation

4. Create installation scripts:
   - setup.sh for Unix-like systems
   - setup.bat for Windows
   - Automatic dependency installation with uv
   - Service registration and configuration

5. Test local scheduling on target platform
6. Ensure automated runs work without user interaction
```

### Step 12: GitHub Actions Integration
**Goal**: Create GitHub Actions workflow for cloud execution

**Prompt**:
```
Create GitHub Actions deployment building on local scheduling:

1. Create .github/workflows/daily-check.yml with:
   - Scheduled trigger for 8 AM daily execution
   - Python 3.10+ environment setup
   - uv installation and dependency management
   - Secure environment variable handling

2. Implement workflow features:
   - Artifact storage for configuration and state
   - Error notification on workflow failures
   - Execution logging and monitoring
   - Manual trigger support for testing

3. Add deployment configuration:
   - Environment-specific config files
   - Secret management for email credentials
   - State persistence between runs
   - Workflow status monitoring

4. Create deployment documentation:
   - Setup instructions for GitHub repository
   - Environment variable configuration
   - Troubleshooting common issues
   - Monitoring and maintenance guide

5. Test GitHub Actions workflow with minimal configuration
6. Verify state persistence and email delivery in cloud environment
```

## Phase 6: Testing and Polish

### Step 13: Comprehensive Testing
**Goal**: Add thorough test coverage for all components

**Prompt**:
```
Implement comprehensive testing building on complete application:

1. Create test infrastructure in tests/:
   - Unit tests for each module (test_config.py, test_scraper.py, etc.)
   - Integration tests for complete workflows
   - Mock services for external dependencies
   - Test data and fixtures

2. Add specific test coverage:
   - Configuration loading and validation
   - Web scraping with various blog types
   - Selector detection accuracy
   - Email formatting and delivery
   - Storage operations and data integrity

3. Create testing utilities:
   - Mock HTTP responses for consistent testing
   - Test blog pages with known structures
   - Email testing with local SMTP server
   - Configuration factories for test scenarios

4. Add test automation:
   - pytest configuration with coverage reporting
   - Continuous integration with GitHub Actions
   - Test matrix for multiple Python versions
   - Performance testing for large blog lists

5. Ensure >90% test coverage across all modules
6. Test error handling and edge cases thoroughly
```

### Step 14: Documentation and Polish
**Goal**: Complete project with documentation and final touches

**Prompt**:
```
Finalize project with comprehensive documentation and polish:

1. Create complete documentation:
   - README.md with installation and usage instructions
   - CONTRIBUTING.md for development setup
   - API documentation for all modules
   - Troubleshooting guide for common issues

2. Add user-friendly features:
   - Configuration wizard for first-time setup
   - Example configurations for popular blogs
   - Migration tools for existing RSS setups
   - Performance optimization for large blog lists

3. Implement monitoring and maintenance:
   - Health check commands for system validation
   - Statistics reporting (success rates, timing)
   - Configuration backup and restore
   - Automated selector validation

4. Create distribution package:
   - PyPI-ready package structure
   - Entry point scripts for easy installation
   - Docker image for containerized deployment
   - Installation packages for major platforms

5. Final testing and validation:
   - End-to-end testing with real blogs
   - Performance testing with large configurations
   - User acceptance testing
   - Security review for credential handling

6. Prepare for production deployment with monitoring and alerting
```

## Implementation Notes

### Key Principles
- **Incremental Progress**: Each step builds on previous work
- **No Orphaned Code**: All code integrates into the main application
- **Safe Implementation**: Small, testable changes at each step
- **Best Practices**: Modern Python patterns and security considerations

### Critical Integration Points
1. **Configuration → Storage**: Ensure consistent data models
2. **Scraper → Detector**: Share page parsing logic
3. **Extractor → Monitor**: Integrate post comparison logic
4. **Monitor → Emailer**: Pass new posts for notification
5. **CLI → All Components**: Orchestrate complete workflows

### Success Validation
Each step should result in:
- ✅ Working, testable code
- ✅ Integration with previous components
- ✅ Clear progress toward final goal
- ✅ No breaking changes to existing functionality
- ✅ Comprehensive error handling
