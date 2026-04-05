"""Performance Tracking & Learning Agent.

Responsibilities:
- Retrieve analytics from YouTube and other platforms.
- Identify top-performing content patterns.
- Generate strategic recommendations via feedback loops.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.analytics import (
    ChannelMetrics,
    ContentPattern,
    PerformanceReport,
    VideoMetrics,
)
from ai_agent.models.content import Platform
from ai_agent.utils.api_clients import YouTubeClient
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a data-driven YouTube content analyst. 
Analyse performance data and extract actionable strategic insights.
Always respond with valid JSON."""


class TrackingAgent:
    """Collects analytics and surfaces performance insights."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMClient] = None,
        youtube: Optional[YouTubeClient] = None,
    ) -> None:
        self._config = config or Config()
        self._llm = llm or LLMClient(self._config)
        self._youtube = youtube or YouTubeClient(self._config)

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def fetch_youtube_channel_metrics(self) -> ChannelMetrics:
        """Pull channel-level statistics from YouTube."""
        logger.info("Fetching YouTube channel metrics.")
        try:
            stats = self._youtube.get_channel_analytics(
                days=self._config.ANALYTICS_LOOKBACK_DAYS
            )
        except Exception as exc:
            logger.warning("Could not fetch YouTube analytics: %s", exc)
            stats = {}

        return ChannelMetrics(
            platform=Platform.YOUTUBE,
            channel_id=self._config.YOUTUBE_CHANNEL_ID,
            total_views=int(stats.get("viewCount", 0)),
            total_subscribers=int(stats.get("subscriberCount", 0)),
        )

    def fetch_video_metrics(self, video_id: str) -> VideoMetrics:
        """Retrieve statistics for a single YouTube video."""
        logger.info("Fetching metrics for video: %s", video_id)
        try:
            data = self._youtube.get_video_stats(video_id)
        except Exception as exc:
            logger.warning("Could not fetch stats for video %s: %s", video_id, exc)
            data = {}

        stats = data.get("statistics", {})
        snippet = data.get("snippet", {})
        return VideoMetrics(
            video_id=video_id,
            platform=Platform.YOUTUBE,
            title=snippet.get("title", ""),
            views=int(stats.get("viewCount", 0)),
            likes=int(stats.get("likeCount", 0)),
            comments=int(stats.get("commentCount", 0)),
            published_at=snippet.get("publishedAt", ""),
        )

    # ------------------------------------------------------------------
    # Pattern analysis
    # ------------------------------------------------------------------

    def extract_content_patterns(
        self, video_metrics: List[VideoMetrics]
    ) -> List[ContentPattern]:
        """Use the LLM to identify recurring patterns among top videos."""
        if not video_metrics:
            return []

        top = sorted(video_metrics, key=lambda v: v.views, reverse=True)[:10]
        summaries = [
            {"title": v.title, "views": v.views, "likes": v.likes, "ctr": v.ctr_percent}
            for v in top
        ]
        prompt = (
            "Analyse these top-performing YouTube videos and extract 3–5 "
            "recurring content patterns (title format, hook style, topic type, etc.).\n"
            f"Data: {summaries}\n\n"
            "Return a JSON array of objects with keys: "
            "pattern_type (string), description (string), examples (list of strings), "
            "avg_ctr_percent (float), avg_views (int), confidence (float 0–1)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        patterns_data: List[Dict[str, Any]] = (
            data if isinstance(data, list) else data.get("patterns", [])
        )
        patterns: List[ContentPattern] = []
        for p in patterns_data:
            if isinstance(p, dict):
                patterns.append(
                    ContentPattern(
                        pattern_type=p.get("pattern_type", ""),
                        description=p.get("description", ""),
                        examples=p.get("examples", []),
                        avg_ctr_percent=float(p.get("avg_ctr_percent", 0.0)),
                        avg_views=int(p.get("avg_views", 0)),
                        confidence=float(p.get("confidence", 0.0)),
                    )
                )
        return patterns

    def generate_strategic_recommendations(
        self, report: PerformanceReport
    ) -> List[str]:
        """Ask the LLM to generate actionable recommendations from the report."""
        summary = {
            "top_patterns": [p.description for p in report.top_patterns],
            "underperforming_topics": report.underperforming_topics,
            "channel_views": sum(
                c.total_views for c in report.channel_metrics
            ),
        }
        prompt = (
            f"Performance summary:\n{summary}\n\n"
            "Generate 5 concrete strategic recommendations to improve YouTube channel "
            "growth and monetisation over the next 30 days. "
            "Return a JSON array of strings."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data if isinstance(data, list) else data.get("recommendations", [])

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self, published_video_ids: Optional[List[str]] = None) -> PerformanceReport:
        """Execute a full tracking cycle and return a PerformanceReport."""
        today = date.today()
        period_start = (today - timedelta(days=self._config.ANALYTICS_LOOKBACK_DAYS)).isoformat()
        period_end = today.isoformat()

        channel_metrics = self.fetch_youtube_channel_metrics()

        video_metrics: List[VideoMetrics] = []
        for vid_id in (published_video_ids or []):
            video_metrics.append(self.fetch_video_metrics(vid_id))

        patterns = self.extract_content_patterns(video_metrics)

        report = PerformanceReport(
            period_start=period_start,
            period_end=period_end,
            channel_metrics=[channel_metrics],
            top_patterns=patterns,
        )
        report.strategic_recommendations = self.generate_strategic_recommendations(report)
        logger.info(
            "Tracking cycle complete. %d patterns identified.", len(patterns)
        )
        return report
