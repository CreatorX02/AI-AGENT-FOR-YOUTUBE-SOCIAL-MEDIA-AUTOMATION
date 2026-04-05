"""SEO & Optimization Agent.

Responsibilities:
- Generate CTR-optimised titles.
- Write SEO-rich descriptions with target keywords.
- Produce relevant tags and platform hashtags.
- Apply YouTube SEO best practices.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import ContentPackage, ContentStatus, Platform, SEOPackage
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a YouTube SEO specialist with expertise in CTR optimisation,
keyword research, and metadata that maximises discoverability.
Always respond with valid JSON in the exact schema requested."""


class SEOAgent:
    """Generates optimised titles, descriptions, tags, and hashtags."""

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

    def optimise_title(self, original_title: str, niche: str) -> str:
        """Return a CTR-optimised version of *original_title*."""
        prompt = (
            f"Niche: {niche}\n"
            f"Original title: {original_title}\n\n"
            "Rewrite this title for maximum CTR on YouTube. "
            "Use proven techniques: numbers, power words, curiosity gaps, "
            "and emotional triggers. Keep it under 70 characters. "
            "Return a JSON object with key: title (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data.get("title", original_title)

    def generate_description(
        self, title: str, script_excerpt: str, niche: str
    ) -> str:
        """Write an SEO-rich YouTube description."""
        prompt = (
            f"Video title: {title}\n"
            f"Niche: {niche}\n"
            f"Script excerpt: {script_excerpt[:400]}\n\n"
            "Write a YouTube description (400–500 words) that:\n"
            "- Starts with the primary keyword in the first sentence\n"
            "- Includes 5–8 relevant secondary keywords naturally\n"
            "- Contains a compelling summary of the video\n"
            "- Includes a CTA (like, subscribe, comment)\n"
            "- Ends with relevant hashtags\n\n"
            "Return a JSON object with key: description (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data.get("description", "")

    def generate_tags(self, title: str, niche: str, count: int = 20) -> List[str]:
        """Generate *count* SEO tags for the video."""
        prompt = (
            f"Video title: {title}\n"
            f"Niche: {niche}\n\n"
            f"Generate {count} highly relevant YouTube tags (mix of short-tail and "
            "long-tail keywords). Return a JSON array of strings."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data if isinstance(data, list) else data.get("tags", [])

    def generate_hashtags(self, title: str, platform: Platform, count: int = 10) -> List[str]:
        """Generate platform-appropriate hashtags."""
        prompt = (
            f"Video title: {title}\n"
            f"Platform: {platform.value}\n\n"
            f"Generate {count} trending, relevant hashtags for this video on {platform.value}. "
            "Do NOT include the # symbol. Return a JSON array of strings."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data if isinstance(data, list) else data.get("hashtags", [])

    def build_seo_package(self, package: ContentPackage) -> SEOPackage:
        """Assemble a full SEO metadata package for *package*."""
        idea = package.idea
        script_excerpt = ""
        if package.script:
            script_excerpt = package.script.hook + " " + package.script.body[:300]

        optimised_title = self.optimise_title(idea.title, idea.niche)
        description = self.generate_description(optimised_title, script_excerpt, idea.niche)
        tags = self.generate_tags(optimised_title, idea.niche)
        hashtags = self.generate_hashtags(optimised_title, Platform.YOUTUBE)

        return SEOPackage(
            title=optimised_title,
            description=description,
            tags=tags,
            hashtags=hashtags,
        )

    def run(self, packages: List[ContentPackage]) -> List[ContentPackage]:
        """Apply SEO optimisation to all packages."""
        for pkg in packages:
            try:
                pkg.seo = self.build_seo_package(pkg)
                if pkg.seo.title:
                    pkg.idea.title = pkg.seo.title
            except Exception as exc:
                logger.error("SEO failed for '%s': %s", pkg.idea.title, exc)
        logger.info("SEO cycle complete for %d packages.", len(packages))
        return packages
