"""Monetization Strategy Agent.

Responsibilities:
- Recommend ad revenue strategies and high-RPM keywords.
- Identify affiliate marketing opportunities.
- Suggest digital product ideas and sponsorship categories.
- Provide niche-specific monetisation plans.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import ContentPackage, MonetizationPlan
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a YouTube monetisation expert. You identify high-RPM niches,
affiliate opportunities, digital products, and sponsorship deals that maximise creator revenue.
Always respond with valid JSON."""


class MonetizationAgent:
    """Generates monetisation strategies for content and channels."""

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

    def analyse_niche_monetization(self, niche: str) -> Dict[str, Any]:
        """Return a detailed monetisation analysis for a niche."""
        logger.info("Analysing monetisation for niche: %s", niche)
        prompt = (
            f"Analyse the '{niche}' niche on YouTube for monetisation potential. "
            "Return a JSON object with keys: "
            "average_rpm_usd (float), "
            "top_ad_keywords (list of strings), "
            "best_affiliate_programs (list of strings), "
            "digital_product_opportunities (list of strings), "
            "sponsorship_categories (list of strings), "
            "estimated_monthly_revenue_per_100k_views_usd (float), "
            "notes (string)."
        )
        return self._llm.complete_json(_SYSTEM_PROMPT, prompt)

    def build_monetization_plan(self, package: ContentPackage) -> MonetizationPlan:
        """Build a tailored monetisation plan for *package*."""
        idea = package.idea
        logger.info("Building monetisation plan for '%s'", idea.title)
        prompt = (
            f"Video title: {idea.title}\n"
            f"Niche: {idea.niche}\n"
            f"Estimated RPM: ${idea.estimated_rpm:.2f}\n\n"
            "Create a monetisation plan for this video. "
            "Return a JSON object with keys: "
            "ad_revenue_keywords (list of strings), "
            "affiliate_suggestions (list of strings), "
            "digital_product_ideas (list of strings), "
            "sponsorship_categories (list of strings), "
            "estimated_monthly_revenue_usd (float), "
            "notes (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return MonetizationPlan(
            ad_revenue_keywords=data.get("ad_revenue_keywords", []),
            affiliate_suggestions=data.get("affiliate_suggestions", []),
            digital_product_ideas=data.get("digital_product_ideas", []),
            sponsorship_categories=data.get("sponsorship_categories", []),
            estimated_monthly_revenue_usd=float(
                data.get("estimated_monthly_revenue_usd", 0.0)
            ),
            notes=data.get("notes", ""),
        )

    def identify_high_rpm_keywords(self, niches: List[str]) -> List[Dict[str, Any]]:
        """Return high-RPM keywords across all *niches*."""
        logger.info("Identifying high-RPM keywords for niches: %s", niches)
        prompt = (
            f"For these niches: {', '.join(niches)}, identify the top 10 YouTube "
            "keywords with the highest advertiser CPM / RPM. "
            "Return a JSON array of objects with keys: "
            "keyword (string), estimated_rpm_usd (float), niche (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        return data if isinstance(data, list) else data.get("keywords", [])

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(self, packages: List[ContentPackage]) -> List[ContentPackage]:
        """Attach monetisation plans to all packages."""
        for pkg in packages:
            try:
                pkg.monetization = self.build_monetization_plan(pkg)
            except Exception as exc:
                logger.error(
                    "Monetisation failed for '%s': %s", pkg.idea.title, exc
                )
        logger.info("Monetisation cycle complete for %d packages.", len(packages))
        return packages
