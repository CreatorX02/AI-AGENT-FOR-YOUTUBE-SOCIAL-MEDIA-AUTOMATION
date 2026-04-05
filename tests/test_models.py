"""Tests for data models."""

import pytest

from ai_agent.models.content import (
    ContentIdea,
    ContentPackage,
    ContentStatus,
    MonetizationPlan,
    Platform,
    PlatformVariant,
    Script,
    SEOPackage,
    ThumbnailConcept,
    TrendSignal,
    VisualDirection,
)
from ai_agent.models.analytics import (
    ChannelMetrics,
    ContentPattern,
    PerformanceReport,
    VideoMetrics,
)


class TestTrendSignal:
    def test_defaults(self):
        signal = TrendSignal(topic="AI Tools", platform=Platform.YOUTUBE)
        assert signal.topic == "AI Tools"
        assert signal.competition_level == "medium"
        assert signal.rpm_potential == "medium"
        assert signal.source_url == ""

    def test_custom_values(self):
        signal = TrendSignal(
            topic="Finance Tips",
            platform=Platform.TIKTOK,
            estimated_search_volume=50000,
            competition_level="low",
            rpm_potential="high",
        )
        assert signal.estimated_search_volume == 50000
        assert signal.competition_level == "low"


class TestContentIdea:
    def test_defaults(self):
        idea = ContentIdea(title="Test Video", niche="finance")
        assert idea.title == "Test Video"
        assert idea.niche == "finance"
        assert idea.hook == ""
        assert idea.target_platforms == []
        assert idea.estimated_rpm == 0.0
        assert idea.priority_score == 0.0

    def test_with_values(self):
        idea = ContentIdea(
            title="How to Save $10k",
            niche="finance",
            hook="Most people waste money on this one thing…",
            estimated_rpm=8.5,
            priority_score=9.2,
        )
        assert idea.estimated_rpm == 8.5
        assert idea.priority_score == 9.2


class TestScript:
    def test_creation(self):
        script = Script(
            title="AI Tools 2025",
            hook="Stop wasting hours on tasks AI can do in seconds.",
            body="Here are the top 5 AI tools that will change your life...",
            call_to_action="Like and subscribe for more AI tips.",
            estimated_duration_seconds=480,
        )
        assert script.title == "AI Tools 2025"
        assert script.estimated_duration_seconds == 480
        assert script.platform == Platform.YOUTUBE


class TestVisualDirection:
    def test_add_scene(self):
        vd = VisualDirection()
        vd.add_scene("0:00", "Host talking to camera", "Office background B-roll")
        vd.add_scene("0:30", "Screen recording of AI tool")
        assert len(vd.scenes) == 2
        assert vd.scenes[0]["timestamp"] == "0:00"
        assert vd.scenes[0]["b_roll"] == "Office background B-roll"
        assert vd.scenes[1]["b_roll"] == ""


class TestSEOPackage:
    def test_creation(self):
        seo = SEOPackage(
            title="5 AI Tools That Will Make You Rich in 2025",
            description="In this video, we explore the top AI tools...",
            tags=["ai tools", "make money online", "passive income"],
            hashtags=["AITools", "MakeMoneyOnline"],
        )
        assert len(seo.tags) == 3
        assert len(seo.hashtags) == 2


class TestThumbnailConcept:
    def test_defaults(self):
        thumb = ThumbnailConcept(
            headline_text="I Made $10k With AI",
            background_description="Dark background with gold coins",
        )
        assert thumb.emotion == "curiosity"
        assert thumb.color_scheme == ""


class TestMonetizationPlan:
    def test_defaults(self):
        plan = MonetizationPlan()
        assert plan.ad_revenue_keywords == []
        assert plan.estimated_monthly_revenue_usd == 0.0

    def test_with_data(self):
        plan = MonetizationPlan(
            ad_revenue_keywords=["best investment", "passive income"],
            affiliate_suggestions=["Robinhood", "Coinbase"],
            estimated_monthly_revenue_usd=1500.0,
        )
        assert plan.estimated_monthly_revenue_usd == 1500.0


class TestPlatformVariant:
    def test_creation(self):
        variant = PlatformVariant(
            platform=Platform.TIKTOK,
            caption="Check out these AI tools! 🔥",
            hashtags=["AI", "TikTok"],
            aspect_ratio="9:16",
            max_duration_seconds=180,
        )
        assert variant.platform == Platform.TIKTOK
        assert variant.aspect_ratio == "9:16"


class TestContentPackage:
    def test_defaults(self):
        idea = ContentIdea(title="Test", niche="tech")
        pkg = ContentPackage(idea=idea)
        assert pkg.status == ContentStatus.IDEA
        assert pkg.script is None
        assert pkg.platform_variants == []


class TestVideoMetrics:
    def test_defaults(self):
        vm = VideoMetrics(
            video_id="abc123", platform=Platform.YOUTUBE, title="My Video"
        )
        assert vm.views == 0
        assert vm.rpm == 0.0


class TestChannelMetrics:
    def test_defaults(self):
        cm = ChannelMetrics(platform=Platform.YOUTUBE, channel_id="UC123")
        assert cm.total_views == 0
        assert cm.top_videos == []


class TestContentPattern:
    def test_creation(self):
        cp = ContentPattern(
            pattern_type="title_format",
            description="Listicle titles with numbers perform best",
            examples=["5 AI Tools", "10 Ways to Save Money"],
            avg_ctr_percent=7.5,
            avg_views=100000,
            confidence=0.85,
        )
        assert cp.confidence == 0.85


class TestPerformanceReport:
    def test_creation(self):
        report = PerformanceReport(
            period_start="2025-01-01",
            period_end="2025-01-31",
        )
        assert report.channel_metrics == []
        assert report.strategic_recommendations == []
