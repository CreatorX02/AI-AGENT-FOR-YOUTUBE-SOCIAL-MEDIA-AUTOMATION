"""Video Creation Pipeline Agent.

Responsibilities:
- Generate original scripts (hook → curiosity → value → payoff).
- Produce scene-by-scene visual direction and B-roll suggestions.
- Suggest voiceover and editing tool integrations.
- Support YouTube long-form, Shorts, TikTok, and Reels formats.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import (
    ContentPackage,
    Platform,
    Script,
    ThumbnailConcept,
    VisualDirection,
)
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert YouTube scriptwriter and video director.
You create original, high-retention scripts using the hook→curiosity→value→payoff framework.
You NEVER copy existing content. Always respond with valid JSON."""

# Platform-specific constraints
_PLATFORM_LIMITS: Dict[Platform, Dict[str, Any]] = {
    Platform.YOUTUBE: {"max_duration": 1200, "aspect_ratio": "16:9", "min_duration": 480},
    Platform.YOUTUBE_SHORTS: {"max_duration": 60, "aspect_ratio": "9:16", "min_duration": 15},
    Platform.TIKTOK: {"max_duration": 180, "aspect_ratio": "9:16", "min_duration": 15},
    Platform.INSTAGRAM_REELS: {"max_duration": 90, "aspect_ratio": "9:16", "min_duration": 15},
    Platform.FACEBOOK: {"max_duration": 1200, "aspect_ratio": "16:9", "min_duration": 30},
    Platform.TWITTER: {"max_duration": 140, "aspect_ratio": "16:9", "min_duration": 5},
}


class CreationAgent:
    """Generates scripts, visual directions, and thumbnail concepts."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMClient] = None,
    ) -> None:
        self._config = config or Config()
        self._llm = llm or LLMClient(self._config)

    # ------------------------------------------------------------------
    # Script generation
    # ------------------------------------------------------------------

    def generate_script(
        self, package: ContentPackage, platform: Platform = Platform.YOUTUBE
    ) -> Script:
        """Generate a full original script for *package* targeting *platform*."""
        limits = _PLATFORM_LIMITS.get(platform, _PLATFORM_LIMITS[Platform.YOUTUBE])
        idea = package.idea
        logger.info("Generating script for '%s' on %s", idea.title, platform.value)

        prompt = (
            f"Title: {idea.title}\n"
            f"Niche: {idea.niche}\n"
            f"Hook concept: {idea.hook}\n"
            f"Platform: {platform.value}\n"
            f"Target duration: {limits['min_duration']}–{limits['max_duration']} seconds\n\n"
            "Write an ORIGINAL script using this structure:\n"
            "1. HOOK (first 3–5 seconds, pattern interrupt)\n"
            "2. CURIOSITY LOOP (tease the payoff)\n"
            "3. VALUE DELIVERY (main content)\n"
            "4. PAYOFF & CTA\n\n"
            "Return a JSON object with keys: hook (string), body (string), "
            "call_to_action (string), estimated_duration_seconds (int)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return Script(
            title=idea.title,
            hook=data.get("hook", ""),
            body=data.get("body", ""),
            call_to_action=data.get("call_to_action", ""),
            estimated_duration_seconds=int(data.get("estimated_duration_seconds", 0)),
            platform=platform,
        )

    # ------------------------------------------------------------------
    # Visual direction
    # ------------------------------------------------------------------

    def generate_visual_direction(self, script: Script) -> VisualDirection:
        """Create a scene-by-scene visual guide with B-roll suggestions."""
        logger.info("Generating visual direction for '%s'", script.title)
        prompt = (
            f"Script hook: {script.hook}\n"
            f"Script body (excerpt): {script.body[:500]}\n\n"
            "Create a scene-by-scene visual direction plan. "
            "Return a JSON array of objects with keys: "
            "timestamp (string, e.g. '0:00'), description (string), b_roll (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        scenes: List[Dict[str, Any]] = data if isinstance(data, list) else data.get("scenes", [])
        vd = VisualDirection()
        for scene in scenes:
            if isinstance(scene, dict):
                vd.add_scene(
                    timestamp=scene.get("timestamp", ""),
                    description=scene.get("description", ""),
                    b_roll=scene.get("b_roll", ""),
                )
        return vd

    # ------------------------------------------------------------------
    # Thumbnail
    # ------------------------------------------------------------------

    def generate_thumbnail_concept(self, package: ContentPackage) -> ThumbnailConcept:
        """Produce a high-CTR thumbnail concept."""
        idea = package.idea
        logger.info("Generating thumbnail concept for '%s'", idea.title)
        prompt = (
            f"Video title: {idea.title}\n"
            f"Hook: {idea.hook}\n\n"
            "Design a YouTube thumbnail concept optimised for high CTR. "
            "Return a JSON object with keys: headline_text (string), "
            "background_description (string), emotion (string), "
            "color_scheme (string), notes (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return ThumbnailConcept(
            headline_text=data.get("headline_text", ""),
            background_description=data.get("background_description", ""),
            emotion=data.get("emotion", "curiosity"),
            color_scheme=data.get("color_scheme", ""),
            notes=data.get("notes", ""),
        )

    # ------------------------------------------------------------------
    # Voiceover / editing recommendations
    # ------------------------------------------------------------------

    def recommend_tools(self, platform: Platform) -> Dict[str, List[str]]:
        """Suggest AI voiceover and video editing tools for *platform*."""
        prompt = (
            f"Recommend the best AI voiceover and video editing tools for "
            f"creating {platform.value} content. "
            "Return a JSON object with keys: voiceover_tools (list of strings), "
            "editing_tools (list of strings), tips (list of strings)."
        )
        return self._llm.complete_json(_SYSTEM_PROMPT, prompt)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self, packages: List[ContentPackage]) -> List[ContentPackage]:
        """Generate scripts, visuals, and thumbnails for all packages."""
        for pkg in packages:
            try:
                script = self.generate_script(pkg)
                pkg.script = script
                pkg.visual_direction = self.generate_visual_direction(script)
                pkg.thumbnail = self.generate_thumbnail_concept(pkg)
            except Exception as exc:
                logger.error("Creation failed for '%s': %s", pkg.idea.title, exc)
        logger.info("Creation cycle complete for %d packages.", len(packages))
        return packages
