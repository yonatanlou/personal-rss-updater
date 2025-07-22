"""Configuration management for the RSS updater application."""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, EmailStr, Field, validator


class EmailConfig(BaseModel):
    """Email notification configuration."""

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    recipient: EmailStr

    @validator("username", always=True)
    def get_username_from_env(cls, v):
        """Get username from environment if not provided."""
        return v or os.getenv("EMAIL_USERNAME")

    @validator("password", always=True)
    def get_password_from_env(cls, v):
        """Get password from environment if not provided."""
        return v or os.getenv("EMAIL_PASSWORD")


class BlogConfig(BaseModel):
    """Configuration for a single blog."""

    name: str
    url: str
    selectors: Dict[str, str] = Field(default_factory=dict)
    last_post_title: Optional[str] = None
    last_post_url: Optional[str] = None
    failure_count: int = 0
    enabled: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""

    email: EmailConfig
    blogs: List[BlogConfig] = Field(default_factory=list)
    retry_count: int = 3
    failure_threshold: int = 3
    user_agent: str = "Mozilla/5.0 (Personal RSS Updater)"
    request_delay: float = 1.0


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from YAML file with environment variable overrides."""
    if config_path is None:
        config_path = Path("config/app/config.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    try:
        return AppConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


def create_sample_config(config_path: Optional[Path] = None) -> None:
    """Create a sample configuration file."""
    if config_path is None:
        config_path = Path("config/app/config.yaml")

    sample_config = {
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "recipient": "your-email@example.com",
        },
        "blogs": [],
        "retry_count": 3,
        "failure_threshold": 3,
        "user_agent": "Mozilla/5.0 (Personal RSS Updater)",
        "request_delay": 1.0,
    }

    with open(config_path, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    print(f"Sample configuration created at: {config_path}")
    print(
        "Please edit the configuration file and set EMAIL_USERNAME and EMAIL_PASSWORD environment variables."
    )


def mask_sensitive_data(config: AppConfig) -> Dict:
    """Return configuration with sensitive data masked for logging."""
    config_dict = config.dict()

    if config_dict.get("email", {}).get("username"):
        config_dict["email"]["username"] = "***masked***"
    if config_dict.get("email", {}).get("password"):
        config_dict["email"]["password"] = "***masked***"

    return config_dict
