# Personal RSS Updater - Technical Specification

## Overview
A robust Python program that monitors blogs (both RSS and non-RSS) for new posts and sends daily email digest notifications. The system uses intelligent web scraping to detect blog post structures automatically and provides a unified monitoring solution.

## Core Requirements

### Functional Requirements
- **Daily Monitoring**: Check configured blogs once daily for new posts
- **Universal Blog Support**: Handle both RSS-enabled and non-RSS blogs through web scraping
- **Email Notifications**: Send daily digest emails with all new posts found
- **Intelligent Detection**: Automatically detect blog post selectors for new blogs
- **Data Persistence**: Track latest posts using JSON storage
- **Deployment Flexibility**: Run locally or via GitHub Actions

### Technical Requirements
- **Python Version**: 3.10+
- **Dependency Management**: Use `uv` for modern Python package management
- **Configuration**: YAML/JSON config file for blogs and settings
- **Error Handling**: Robust failure detection and notification system

## System Architecture

### Core Components

1. **Blog Manager**
   - OPML import functionality
   - Blog configuration management
   - Selector detection and validation

2. **Web Scraper**
   - Intelligent post detection
   - Generic CSS selector approach
   - Retry logic for network failures

3. **Post Tracker**
   - JSON-based storage of latest posts per blog
   - New post detection logic
   - Change comparison system

4. **Email Notifier**
   - SMTP integration with environment variables
   - Daily digest formatting
   - Single recipient delivery

5. **Scheduler**
   - GitHub Actions integration for 8 AM daily runs
   - Local execution flexibility (manual/scheduled)

## Detailed Specifications

### Blog Post Detection
- **Method**: Generic CSS selector detection
- **Auto-Detection**: Analyze blog structure to identify post containers
- **Validation Workflow**: 
  1. Automatically detect selectors
  2. Present findings to user for confirmation
  3. Save validated selectors to configuration
- **Fallback**: Manual selector configuration when auto-detection fails

### New Post Logic
- **Storage**: Store latest post title/identifier per blog in JSON
- **Detection**: Compare current latest post with stored version
- **Trigger**: Different latest post = new content detected

### Email Digest Format
**Daily digest containing:**
- Post title
- Direct link to post
- Blog name/source
- Publication date (if detectable)
- Brief excerpt/summary (if extractable)
- **Organization**: Chronological order (newest first)
- **Delivery**: Single email per day to configured recipient

### Error Handling

**Network/Availability Issues:**
- Retry failed blogs 2-3 times during same run
- Log failures for monitoring

**Persistent Failures:**
- Email warning after 3+ consecutive days of blog failures
- Continue monitoring other blogs

**Structure Changes:**
- Notify user when existing selectors break
- Require manual intervention (no automatic re-detection)
- Provide tools to update/fix selectors

### Configuration Management

**Config File Structure (YAML/JSON):**
```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  recipient: user@example.com
  # Credentials via environment variables

blogs:
  - name: "Blog Name"
    url: "https://example.com"
    selectors:
      title: ".post-title"
      link: ".post-link"
      date: ".post-date"
    last_post: "stored-post-identifier"
```

**Environment Variables:**
- `EMAIL_USERNAME`: SMTP authentication username
- `EMAIL_PASSWORD`: SMTP authentication password

### Deployment Options

**Local Execution:**
- Manual runs via CLI command
- Optional local scheduling (cron/task scheduler)
- Development and testing mode

**GitHub Actions:**
- Scheduled workflow for 8 AM daily execution
- Secure environment variable management
- Automated dependency installation with uv

### Initial Setup Workflow

1. **OPML Import**: Parse existing subscriptions-2025-07-12 file
2. **Bulk Detection**: Attempt auto-detection for all ~25 blogs
3. **Validation Phase**: Present detected selectors for each blog
4. **Configuration Save**: Store validated selectors in config file
5. **Initial Run**: Establish baseline (store current latest posts)
6. **Schedule Setup**: Configure daily monitoring

## Implementation Phases

### Phase 1: Core Infrastructure
- Project setup with uv
- Basic web scraping framework
- JSON storage system
- Configuration management

### Phase 2: Intelligence Layer
- Automatic selector detection algorithm
- Validation interface
- OPML import functionality

### Phase 3: Communication
- Email notification system
- Digest formatting
- Error notification system

### Phase 4: Deployment
- GitHub Actions workflow
- Local execution scripts
- Documentation and setup guides

### Phase 5: Integration & Testing
- End-to-end testing with real blogs
- Error handling validation
- Performance optimization

## Success Criteria
- Successfully monitor all ~25 existing blogs from OPML
- Reliable daily digest delivery at 8 AM
- < 5% false positives/negatives for new post detection
- Graceful handling of blog downtime and structure changes
- Easy addition of new blogs with minimal manual configuration
- Successful deployment in both local and GitHub Actions environments

## Maintenance Considerations
- Periodic review of selector accuracy
- Blog health monitoring
- Performance optimization for scale
- Security updates for dependencies