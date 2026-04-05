"""Automated Distribution Agent.

Responsibilities:
- Upload/publish content to YouTube, TikTok, Instagram, Facebook, and X.
- Customise captions and formatting per platform.
- Schedule posts at optimal engagement times.
- Ensure platform-specific aspect ratios, durations, and caption limits.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_agent.config import Config
from ai_agent.models.content import (
    ContentPackage,
    ContentStatus,
    Platform,
    PlatformVariant,
)
from ai_agent.utils.api_clients import (
    FacebookClient,
    InstagramClient,
    TikTokClient,
    TwitterClient,
    YouTubeClient,
)
from ai_agent.utils.llm import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a social media distribution specialist.
You adapt video content for each platform's unique audience and format requirements.
Always respond with valid JSON."""

# Maximum caption lengths per platform (characters)
_CAPTION_LIMITS: Dict[Platform, int] = {
    Platform.YOUTUBE: 5000,
    Platform.YOUTUBE_SHORTS: 500,
    Platform.TIKTOK: 2200,
    Platform.INSTAGRAM_REELS: 2200,
    Platform.FACEBOOK: 63206,
    Platform.TWITTER: 280,
}


class DistributionAgent:
    """Distributes content packages across all configured social platforms."""

    def __init__(
        self,
        config: Optional[Config] = None,
        llm: Optional[LLMClient] = None,
        youtube: Optional[YouTubeClient] = None,
        tiktok: Optional[TikTokClient] = None,
        instagram: Optional[InstagramClient] = None,
        facebook: Optional[FacebookClient] = None,
        twitter: Optional[TwitterClient] = None,
    ) -> None:
        self._config = config or Config()
        self._llm = llm or LLMClient(self._config)
        self._youtube = youtube or YouTubeClient(self._config)
        self._tiktok = tiktok or TikTokClient(self._config)
        self._instagram = instagram or InstagramClient(self._config)
        self._facebook = facebook or FacebookClient(self._config)
        self._twitter = twitter or TwitterClient(self._config)

    # ------------------------------------------------------------------
    # Caption adaptation
    # ------------------------------------------------------------------

    def adapt_caption(self, package: ContentPackage, platform: Platform) -> str:
        """Generate a platform-specific caption for *package*."""
        seo_desc = package.seo.description if package.seo else ""
        prompt = (
            f"Video title: {package.idea.title}\n"
            f"Platform: {platform.value}\n"
            f"Character limit: {_CAPTION_LIMITS.get(platform, 500)}\n"
            f"Base description: {seo_desc[:300]}\n\n"
            f"Write an engaging, platform-native caption for {platform.value}. "
            "Match the platform's tone and culture. Stay within the character limit. "
            "Return a JSON object with key: caption (string)."
        )
        data = self._llm.complete_json(_SYSTEM_PROMPT, prompt)
        caption = data.get("caption", package.idea.title)
        limit = _CAPTION_LIMITS.get(platform, 500)
        return caption[:limit]

    def build_platform_variants(self, package: ContentPackage) -> List[PlatformVariant]:
        """Build per-platform distribution variants for *package*."""
        variants: List[PlatformVariant] = []
        for platform in Platform:
            caption = self.adapt_caption(package, platform)
            hashtags = package.seo.hashtags[:10] if package.seo else []
            variants.append(
                PlatformVariant(
                    platform=platform,
                    caption=caption,
                    hashtags=hashtags,
                    aspect_ratio="9:16" if platform in (
                        Platform.YOUTUBE_SHORTS,
                        Platform.TIKTOK,
                        Platform.INSTAGRAM_REELS,
                    ) else "16:9",
                )
            )
        return variants

    # ------------------------------------------------------------------
    # Per-platform publishing helpers
    # ------------------------------------------------------------------

    def publish_to_youtube(
        self, package: ContentPackage, video_file_path: str
    ) -> str:
        """Upload a video to YouTube and return the video ID."""
        seo = package.seo
        return self._youtube.upload_video(
            file_path=video_file_path,
            title=seo.title if seo else package.idea.title,
            description=seo.description if seo else "",
            tags=seo.tags if seo else [],
        )

    def publish_to_tiktok(
        self, package: ContentPackage, video_url: str
    ) -> Dict[str, Any]:
        """Post a video to TikTok."""
        variant = next(
            (v for v in package.platform_variants if v.platform == Platform.TIKTOK),
            None,
        )
        caption = variant.caption if variant else package.idea.title
        hashtags = variant.hashtags if variant else []
        return self._tiktok.upload_video(
            video_url=video_url, caption=caption, hashtags=hashtags
        )

    def publish_to_instagram(
        self, package: ContentPackage, video_url: str
    ) -> Dict[str, Any]:
        """Post a Reel to Instagram."""
        variant = next(
            (v for v in package.platform_variants if v.platform == Platform.INSTAGRAM_REELS),
            None,
        )
        caption = variant.caption if variant else package.idea.title
        return self._instagram.upload_reel(video_url=video_url, caption=caption)

    def publish_to_facebook(
        self, package: ContentPackage, video_url: str
    ) -> Dict[str, Any]:
        """Post a video to Facebook."""
        seo = package.seo
        return self._facebook.upload_video(
            video_url=video_url,
            title=seo.title if seo else package.idea.title,
            description=seo.description[:500] if seo else "",
        )

    def publish_to_twitter(self, package: ContentPackage) -> Dict[str, Any]:
        """Post a promotional tweet for the video."""
        variant = next(
            (v for v in package.platform_variants if v.platform == Platform.TWITTER),
            None,
        )
        text = variant.caption if variant else package.idea.title
        return self._twitter.post_tweet(text)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(
        self, packages: List[ContentPackage], video_file_paths: Optional[Dict[str, str]] = None
    ) -> List[ContentPackage]:
        """Build platform variants for all packages.

        Actual uploads require *video_file_paths* mapping idea title → local path.
        When paths are provided the agent attempts to publish to each platform.
        """
        video_file_paths = video_file_paths or {}
        for pkg in packages:
            try:
                pkg.platform_variants = self.build_platform_variants(pkg)
            except Exception as exc:
                logger.error("Variant generation failed for '%s': %s", pkg.idea.title, exc)

            file_path = video_file_paths.get(pkg.idea.title)
            if file_path:
                try:
                    self.publish_to_youtube(pkg, file_path)
                    pkg.status = ContentStatus.PUBLISHED
                except Exception as exc:
                    logger.error("YouTube publish failed for '%s': %s", pkg.idea.title, exc)

        logger.info("Distribution cycle complete for %d packages.", len(packages))
        return packages
