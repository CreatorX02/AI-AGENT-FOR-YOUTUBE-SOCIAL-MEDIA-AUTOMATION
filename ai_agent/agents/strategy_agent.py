"""Content Strategy & Planning Agent.

Responsibilities:
- Build weekly and monthly content calendars.
- Prioritise niches with high monetisation potential.
- Optimise for both virality and evergreen traffic.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import ContentIdea, ContentPackage, ContentStatus, Platform
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a YouTube content strategist with deep knowledge of
viral content mechanics and long-term channel growth. Respond with valid JSON."""


class StrategyAgent:
    """Builds content calendars and prioritises ideas for maximum impact."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self._config = config or Config()
        self._llm = llm or LLMClient(self._config)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def prioritise_ideas(self, ideas: List[ContentIdea]) -> List[ContentIdea]:
        """Re-score and sort ideas using LLM-driven strategic analysis."""
        if not ideas:
            return ideas

        logger.info("Prioritising %d content ideas.", len(ideas))
        idea_summaries = [
            {"title": i.title, "niche": i.niche, "estimated_rpm": i.estimated_rpm}
            for i in ideas
        ]
        prompt = (
            "Score each content idea for strategic value (virality + evergreen "
            "potential + RPM). Return a JSON array of objects with keys: "
            "title (string) and priority_score (float 0–10), in descending order. "
            f"Ideas:\n{idea_summaries}"
        )
        scored = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        scored_list: List[Dict[str, Any]] = (
            scored if isinstance(scored, list) else scored.get("ideas", [])
        )
        score_map: Dict[str, float] = {
            s["title"]: float(s.get("priority_score", 0.0))
            for s in scored_list
            if isinstance(s, dict)
        }
        for idea in ideas:
            if idea.title in score_map:
                idea.priority_score = score_map[idea.title]
        ideas.sort(key=lambda x: x.priority_score, reverse=True)
        return ideas

    def build_weekly_calendar(
        self, ideas: List[ContentIdea], start_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Assign top ideas to publication slots across 7 days."""
        start = start_date or date.today()
        calendar_entries: List[Dict[str, Any]] = []
        platforms_cycle = [
            Platform.YOUTUBE,
            Platform.YOUTUBE_SHORTS,
            Platform.TIKTOK,
            Platform.INSTAGRAM_REELS,
            Platform.YOUTUBE,
            Platform.YOUTUBE_SHORTS,
            Platform.FACEBOOK,
        ]
        for i, day_offset in enumerate(range(7)):
            publish_date = start + timedelta(days=day_offset)
            idea = ideas[i % len(ideas)] if ideas else None
            platform = platforms_cycle[i % len(platforms_cycle)]
            calendar_entries.append(
                {
                    "date": publish_date.isoformat(),
                    "platform": platform.value,
                    "idea_title": idea.title if idea else "",
                    "niche": idea.niche if idea else "",
                }
            )
        return calendar_entries

    def build_monthly_calendar(
        self, ideas: List[ContentIdea], year: Optional[int] = None, month: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Distribute ideas across every day of the target month."""
        today = date.today()
        target_year = year or today.year
        target_month = month or today.month
        _, days_in_month = calendar.monthrange(target_year, target_month)
        start = date(target_year, target_month, 1)
        return self.build_weekly_calendar(ideas, start_date=start)[:days_in_month]

    def recommend_optimal_post_times(self, platform: Platform) -> List[str]:
        """Return LLM-suggested optimal posting times for *platform*."""
        prompt = (
            f"For the {platform.value} platform, list the 3 optimal times to post "
            "content for maximum engagement (e.g. 'Tuesday 18:00 EST'). "
            "Return a JSON array of strings."
        )
        result = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return result if isinstance(result, list) else result.get("times", [])

    def create_packages(self, ideas: List[ContentIdea]) -> List[ContentPackage]:
        """Wrap prioritised ideas into ContentPackage containers."""
        return [
            ContentPackage(idea=idea, status=ContentStatus.IDEA) for idea in ideas
        ]

    def run(self, ideas: List[ContentIdea]) -> List[ContentPackage]:
        """Execute a full strategy cycle: prioritise → calendar → package."""
        prioritised = self.prioritise_ideas(ideas)
        weekly = self.build_weekly_calendar(prioritised)
        logger.info("Weekly calendar built with %d slots.", len(weekly))
        packages = self.create_packages(prioritised)
        logger.info("Strategy cycle complete. %d packages created.", len(packages))
        return packages
