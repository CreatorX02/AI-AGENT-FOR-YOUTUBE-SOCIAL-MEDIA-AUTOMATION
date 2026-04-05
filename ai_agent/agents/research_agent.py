"""Market Research & Trend Analysis Agent.

Responsibilities:
- Browse YouTube and other platforms for trending content.
- Identify high-RPM niches and underserved content gaps.
- Extract content patterns from top-performing videos.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import ContentIdea, Platform, TrendSignal
from ai_agent.utils.api_clients import YouTubeClient
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert YouTube market researcher.
Your job is to identify trending topics, high-RPM niches, and underserved content gaps.
Always respond with valid JSON in the exact schema requested."""


class ResearchAgent:
    """Discovers trending topics and surfaces high-value content opportunities."""

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
    # Public interface
    # ------------------------------------------------------------------

    def fetch_trend_signals(self, niche: str) -> List[TrendSignal]:
        """Query YouTube for trending videos in *niche* and return signals."""
        logger.info("Fetching trend signals for niche: %s", niche)
        try:
            items = self._youtube.search_trending(query=niche, max_results=10)
        except Exception as exc:
            logger.warning("YouTube API error for '%s': %s", niche, exc)
            items = []

        signals: List[TrendSignal] = []
        for item in items:
            snippet = item.get("snippet", {})
            signals.append(
                TrendSignal(
                    topic=snippet.get("title", ""),
                    platform=Platform.YOUTUBE,
                    source_url=(
                        "https://www.youtube.com/watch?v="
                        + item.get("id", {}).get("videoId", "")
                    ),
                )
            )
        return signals

    def analyze_niche(self, niche: str) -> Dict[str, Any]:
        """Use the LLM to analyse a niche for opportunity and RPM potential."""
        logger.info("Analysing niche: %s", niche)
        prompt = (
            f"Analyse the YouTube content niche '{niche}'. "
            "Return a JSON object with keys: "
            "competition_level (low/medium/high), "
            "rpm_potential (low/medium/high), "
            "estimated_monthly_searches (integer), "
            "top_content_patterns (list of strings), "
            "underserved_subtopics (list of strings)."
        )
        return self._llm.complete_json(_SYSTEM_PROMPT, prompt)

    def generate_content_ideas(
        self, niche: str, trend_signals: List[TrendSignal], count: int = 5
    ) -> List[ContentIdea]:
        """Generate original content ideas based on trend signals."""
        logger.info("Generating %d content ideas for niche: %s", count, niche)
        signal_titles = [s.topic for s in trend_signals[:10]]
        prompt = (
            f"Based on these trending YouTube titles in the '{niche}' niche:\n"
            + "\n".join(f"- {t}" for t in signal_titles)
            + f"\n\nGenerate {count} ORIGINAL content ideas. "
            "Return a JSON array where each element has keys: "
            "title (string), hook (string, 1–2 sentences), "
            "estimated_rpm (float, USD), priority_score (float 0–10)."
        )
        result = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        ideas_data: List[Dict[str, Any]] = result if isinstance(result, list) else result.get("ideas", [])
        ideas: List[ContentIdea] = []
        for item in ideas_data:
            if not isinstance(item, dict):
                continue
            ideas.append(
                ContentIdea(
                    title=item.get("title", ""),
                    niche=niche,
                    hook=item.get("hook", ""),
                    estimated_rpm=float(item.get("estimated_rpm", 0.0)),
                    priority_score=float(item.get("priority_score", 0.0)),
                )
            )
        return ideas

    def identify_content_gaps(self, niches: List[str]) -> List[Dict[str, Any]]:
        """Find underserved content gaps across all target niches."""
        logger.info("Identifying content gaps for niches: %s", niches)
        prompt = (
            f"For these YouTube niches: {', '.join(niches)}, "
            "identify the top 5 underserved content gaps with high demand and low competition. "
            "Return a JSON array where each element has keys: "
            "niche (string), gap_topic (string), reason (string), opportunity_score (float 0–10)."
        )
        result = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return result if isinstance(result, list) else result.get("gaps", [])

    def run(self) -> List[ContentIdea]:
        """Execute a full research cycle for all configured niches."""
        all_ideas: List[ContentIdea] = []
        for niche in self._config.TARGET_NICHES:
            signals = self.fetch_trend_signals(niche)
            ideas = self.generate_content_ideas(niche, signals)
            all_ideas.extend(ideas)
        all_ideas.sort(key=lambda x: x.priority_score, reverse=True)
        logger.info("Research cycle complete. %d ideas generated.", len(all_ideas))
        return all_ideas
