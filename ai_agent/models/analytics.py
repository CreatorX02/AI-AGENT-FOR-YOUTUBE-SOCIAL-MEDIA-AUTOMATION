"""Analytics data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ai_agent.models.content import Platform


@dataclass
class VideoMetrics:
    """Performance metrics for a single published video."""

    video_id: str
    platform: Platform
    title: str
    views: int = 0
    watch_time_hours: float = 0.0
    ctr_percent: float = 0.0
    average_view_duration_seconds: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    rpm: float = 0.0
    estimated_revenue_usd: float = 0.0
    published_at: str = ""  # ISO-8601


@dataclass
class ChannelMetrics:
    """Aggregated channel-level performance metrics."""

    platform: Platform
    channel_id: str
    total_views: int = 0
    total_subscribers: int = 0
    total_watch_time_hours: float = 0.0
    average_rpm: float = 0.0
    top_videos: List[VideoMetrics] = field(default_factory=list)
    period_start: str = ""
    period_end: str = ""


@dataclass
class ContentPattern:
    """A recurring pattern extracted from top-performing content."""

    pattern_type: str  # e.g. "title_format", "hook_style", "video_length"
    description: str
    examples: List[str] = field(default_factory=list)
    avg_ctr_percent: float = 0.0
    avg_views: int = 0
    confidence: float = 0.0  # 0.0–1.0


@dataclass
class PerformanceReport:
    """Full performance report used to refine future content strategy."""

    period_start: str
    period_end: str
    channel_metrics: List[ChannelMetrics] = field(default_factory=list)
    top_patterns: List[ContentPattern] = field(default_factory=list)
    underperforming_topics: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
