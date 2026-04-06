"""Main Orchestrator — AI Content Growth Agent.

Execution cycle (continuous):
    Research → Analyse → Create → Publish → Optimise → Repeat

Run directly:
    python -m ai_agent.main

Or as a scheduled daemon:
    python -m ai_agent.main --daemon
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Dict, List, Optional

import schedule

from ai_agent.agents.creation_agent import CreationAgent
from ai_agent.agents.distribution_agent import DistributionAgent
from ai_agent.agents.monetization_agent import MonetizationAgent
from ai_agent.agents.research_agent import ResearchAgent
from ai_agent.agents.seo_agent import SEOAgent
from ai_agent.agents.strategy_agent import StrategyAgent
from ai_agent.agents.tracking_agent import TrackingAgent
from ai_agent.config import Config, get_logger
from ai_agent.models.analytics import PerformanceReport
from ai_agent.models.content import ContentPackage

logger = get_logger(__name__)


class ContentGrowthOrchestrator:
    """Co-ordinates all agents through the full content production cycle."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()
        self._research = ResearchAgent(self._config)
        self._strategy = StrategyAgent(self._config)
        self._creation = CreationAgent(self._config)
        self._seo = SEOAgent(self._config)
        self._distribution = DistributionAgent(self._config)
        self._tracking = TrackingAgent(self._config)
        self._monetization = MonetizationAgent(self._config)

        # State accumulated across cycles
        self._published_video_ids: List[str] = []
        self._last_report: Optional[PerformanceReport] = None

    # ------------------------------------------------------------------
    # Core cycle
    # ------------------------------------------------------------------

    def run_cycle(
        self,
        video_file_paths: Optional[Dict[str, str]] = None,
        video_urls: Optional[Dict[str, str]] = None,
    ) -> List[ContentPackage]:
        """Execute one full Research → Create → Distribute → Track cycle.

        Parameters
        ----------
        video_file_paths:
            Optional mapping of ``{original_title: local_file_path}`` for YouTube
            uploads.  When absent, the pipeline runs up to (and including) the
            distribution *variant-building* step but skips actual uploads.
        video_urls:
            Optional mapping of ``{original_title: hosted_url}`` for TikTok,
            Instagram, and Facebook uploads.
        """
        logger.info("=" * 60)
        logger.info("Starting content growth cycle.")
        logger.info("=" * 60)

        # 1. Research
        logger.info("[1/7] Research & trend analysis …")
        ideas = self._research.run()

        # 2. Strategy
        logger.info("[2/7] Content strategy & planning …")
        packages = self._strategy.run(ideas)

        # 3. Creation
        logger.info("[3/7] Video creation pipeline …")
        packages = self._creation.run(packages)

        # 4. SEO
        logger.info("[4/7] SEO & optimisation …")
        packages = self._seo.run(packages)

        # 5. Monetisation
        logger.info("[5/7] Monetisation strategy …")
        packages = self._monetization.run(packages)

        # 6. Distribution
        logger.info("[6/7] Automated distribution …")
        packages = self._distribution.run(packages, video_file_paths, video_urls)

        # Collect newly published YouTube video IDs for the tracking step.
        for pkg in packages:
            if pkg.youtube_video_id and pkg.youtube_video_id not in self._published_video_ids:
                self._published_video_ids.append(pkg.youtube_video_id)

        # 7. Tracking (uses all previously published IDs)
        logger.info("[7/7] Performance tracking …")
        self._last_report = self._tracking.run(self._published_video_ids)

        self._log_cycle_summary(packages)
        return packages

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def _log_cycle_summary(self, packages: List[ContentPackage]) -> None:
        logger.info("-" * 60)
        logger.info("Cycle summary — %d packages processed:", len(packages))
        for pkg in packages[:5]:  # show top 5
            title = pkg.seo.title if pkg.seo else pkg.idea.title
            rpm = pkg.idea.estimated_rpm
            mon = (
                pkg.monetization.estimated_monthly_revenue_usd
                if pkg.monetization
                else 0.0
            )
            logger.info(
                "  • [%.1f pts] %s | RPM $%.2f | Est. revenue $%.0f/mo",
                pkg.idea.priority_score,
                title,
                rpm,
                mon,
            )
        if self._last_report:
            logger.info(
                "Performance recommendations: %s",
                self._last_report.strategic_recommendations[:2],
            )
        logger.info("-" * 60)

    # ------------------------------------------------------------------
    # Daemon / scheduling
    # ------------------------------------------------------------------

    def start_daemon(self) -> None:
        """Run the content cycle on a recurring schedule (blocking)."""
        interval = self._config.CONTENT_CYCLE_INTERVAL_HOURS
        logger.info(
            "Starting daemon: cycle every %d hour(s). Press Ctrl+C to stop.",
            interval,
        )
        schedule.every(interval).hours.do(self.run_cycle)

        # Run immediately on start
        self.run_cycle()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user.")


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Content Growth Agent — YouTube & Social Media Automation"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously on the configured interval.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)
    orchestrator = ContentGrowthOrchestrator()
    if args.daemon:
        orchestrator.start_daemon()
    else:
        orchestrator.run_cycle()


if __name__ == "__main__":
    main(sys.argv[1:])
