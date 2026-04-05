"""Configuration management for the AI Content Growth Agent."""

import os
import logging
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _get_list(key: str, default: str = "") -> List[str]:
    """Return an env variable as a stripped, non-empty list of strings."""
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    """Central configuration object populated from environment variables."""

    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # YouTube
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_CLIENT_ID: str = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET: str = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    YOUTUBE_CHANNEL_ID: str = os.getenv("YOUTUBE_CHANNEL_ID", "")

    # TikTok
    TIKTOK_ACCESS_TOKEN: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")

    # Instagram / Facebook
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")

    # X (Twitter)
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    TWITTER_ACCESS_SECRET: str = os.getenv("TWITTER_ACCESS_SECRET", "")

    # Agent behaviour
    TARGET_NICHES: List[str] = _get_list(
        "TARGET_NICHES", "finance,AI,technology,health,productivity"
    )
    CONTENT_CYCLE_INTERVAL_HOURS: int = int(
        os.getenv("CONTENT_CYCLE_INTERVAL_HOURS", "24")
    )
    ANALYTICS_LOOKBACK_DAYS: int = int(os.getenv("ANALYTICS_LOOKBACK_DAYS", "30"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def get_logger(name: str) -> logging.Logger:
    """Return a consistently configured logger."""
    config = Config()
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger(name)
