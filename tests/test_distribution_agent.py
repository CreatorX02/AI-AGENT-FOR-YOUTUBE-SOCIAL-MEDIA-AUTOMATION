"""Tests for the Distribution Agent."""

import pytest
from unittest.mock import MagicMock

from ai_agent.agents.distribution_agent import DistributionAgent, _CAPTION_LIMITS
from ai_agent.config import Config
from ai_agent.models.content import (
    ContentIdea,
    ContentPackage,
    ContentStatus,
    Platform,
    SEOPackage,
)


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def agent(mock_llm):
    return DistributionAgent(
        config=Config(),
        llm=mock_llm,
        youtube=MagicMock(),
        tiktok=MagicMock(),
        instagram=MagicMock(),
        facebook=MagicMock(),
        twitter=MagicMock(),
    )


@pytest.fixture
def sample_package():
    idea = ContentIdea(title="AI Money Hacks 2025", niche="AI")
    pkg = ContentPackage(idea=idea)
    pkg.seo = SEOPackage(
        title="AI Money Hacks That Will Make You Rich in 2025",
        description="In this video we explore money-making AI strategies...",
        tags=["ai", "make money", "passive income"],
        hashtags=["AI", "MoneyHacks", "Finance"],
    )
    return pkg


class TestAdaptCaption:
    def test_returns_caption_within_limit(self, agent, mock_llm, sample_package):
        long_caption = "A" * 300
        mock_llm.complete_json.return_value = {"caption": long_caption}
        caption = agent.adapt_caption(sample_package, Platform.TWITTER)
        assert len(caption) <= _CAPTION_LIMITS[Platform.TWITTER]

    def test_returns_title_if_caption_missing(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {}
        caption = agent.adapt_caption(sample_package, Platform.TIKTOK)
        assert caption == sample_package.idea.title

    def test_includes_platform_in_prompt(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {"caption": "Test caption"}
        agent.adapt_caption(sample_package, Platform.INSTAGRAM_REELS)
        call_args = mock_llm.complete_json.call_args[0][1]
        assert "instagram_reels" in call_args


class TestBuildPlatformVariants:
    def test_creates_variant_for_each_platform(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {"caption": "Test caption"}
        variants = agent.build_platform_variants(sample_package)
        platforms = {v.platform for v in variants}
        assert Platform.YOUTUBE in platforms
        assert Platform.TIKTOK in platforms
        assert Platform.INSTAGRAM_REELS in platforms
        assert Platform.TWITTER in platforms

    def test_short_form_platforms_use_vertical_aspect_ratio(
        self, agent, mock_llm, sample_package
    ):
        mock_llm.complete_json.return_value = {"caption": "caption"}
        variants = agent.build_platform_variants(sample_package)
        short_form = {Platform.YOUTUBE_SHORTS, Platform.TIKTOK, Platform.INSTAGRAM_REELS}
        for variant in variants:
            if variant.platform in short_form:
                assert variant.aspect_ratio == "9:16"
            else:
                assert variant.aspect_ratio == "16:9"


class TestPublishToTwitter:
    def test_posts_tweet(self, agent, mock_llm, sample_package):
        agent._twitter.post_tweet.return_value = {"data": {"id": "tweet123"}}
        mock_llm.complete_json.return_value = {"caption": "Check out this AI video!"}
        # Build variants first
        sample_package.platform_variants = agent.build_platform_variants(sample_package)
        result = agent.publish_to_twitter(sample_package)
        agent._twitter.post_tweet.assert_called_once()


class TestRun:
    def test_run_builds_variants(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {"caption": "Caption"}
        packages = agent.run([sample_package])
        assert len(packages[0].platform_variants) == len(list(Platform))

    def test_run_without_file_paths_skips_upload(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {"caption": "Caption"}
        packages = agent.run([sample_package])
        agent._youtube.upload_video.assert_not_called()
        assert packages[0].status != ContentStatus.PUBLISHED

    def test_run_handles_variant_generation_error(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.side_effect = Exception("LLM error")
        packages = agent.run([sample_package])
        assert packages[0].platform_variants == []
