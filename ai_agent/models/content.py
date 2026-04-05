"""Content data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class Platform(str, Enum):
    YOUTUBE = "youtube"
    YOUTUBE_SHORTS = "youtube_shorts"
    TIKTOK = "tiktok"
    INSTAGRAM_REELS = "instagram_reels"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class ContentStatus(str, Enum):
    IDEA = "idea"
    SCRIPTED = "scripted"
    PRODUCED = "produced"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


@dataclass
class TrendSignal:
    """A trending topic or content pattern detected during research."""

    topic: str
    platform: Platform
    estimated_search_volume: int = 0
    competition_level: str = "medium"  # low / medium / high
    rpm_potential: str = "medium"      # low / medium / high
    source_url: str = ""
    notes: str = ""


@dataclass
class ContentIdea:
    """A single content idea generated from trend research."""

    title: str
    niche: str
    hook: str = ""
    target_platforms: List[Platform] = field(default_factory=list)
    trend_signals: List[TrendSignal] = field(default_factory=list)
    estimated_rpm: float = 0.0
    priority_score: float = 0.0


@dataclass
class Script:
    """A full video script generated for a content idea."""

    title: str
    hook: str
    body: str
    call_to_action: str
    estimated_duration_seconds: int = 0
    platform: Platform = Platform.YOUTUBE


@dataclass
class VisualDirection:
    """Scene-by-scene visual and B-roll suggestions."""

    scenes: List[Dict[str, str]] = field(default_factory=list)
    # Each scene dict: {"timestamp": "0:00", "description": "...", "b_roll": "..."}

    def add_scene(
        self, timestamp: str, description: str, b_roll: str = ""
    ) -> None:
        self.scenes.append(
            {"timestamp": timestamp, "description": description, "b_roll": b_roll}
        )


@dataclass
class ThumbnailConcept:
    """High-CTR thumbnail idea."""

    headline_text: str
    background_description: str
    emotion: str = "curiosity"
    color_scheme: str = ""
    notes: str = ""


@dataclass
class SEOPackage:
    """SEO metadata for a video."""

    title: str
    description: str
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)


@dataclass
class PlatformVariant:
    """Platform-specific adaptation of a piece of content."""

    platform: Platform
    caption: str
    hashtags: List[str] = field(default_factory=list)
    aspect_ratio: str = "16:9"
    max_duration_seconds: Optional[int] = None
    scheduled_time: Optional[str] = None  # ISO-8601 string


@dataclass
class MonetizationPlan:
    """Recommended monetization strategy for a video/niche."""

    ad_revenue_keywords: List[str] = field(default_factory=list)
    affiliate_suggestions: List[str] = field(default_factory=list)
    digital_product_ideas: List[str] = field(default_factory=list)
    sponsorship_categories: List[str] = field(default_factory=list)
    estimated_monthly_revenue_usd: float = 0.0
    notes: str = ""


@dataclass
class ContentPackage:
    """Complete content package ready for production and distribution."""

    idea: ContentIdea
    script: Optional[Script] = None
    visual_direction: Optional[VisualDirection] = None
    thumbnail: Optional[ThumbnailConcept] = None
    seo: Optional[SEOPackage] = None
    platform_variants: List[PlatformVariant] = field(default_factory=list)
    monetization: Optional[MonetizationPlan] = None
    status: ContentStatus = ContentStatus.IDEA
