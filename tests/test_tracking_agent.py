"""Tests for the Tracking Agent."""

import pytest
from unittest.mock import MagicMock

from ai_agent.agents.tracking_agent import TrackingAgent
from ai_agent.config import Config
from ai_agent.models.analytics import (
    ChannelMetrics,
    ContentPattern,
    PerformanceReport,
    VideoMetrics,
)
from ai_agent.models.content import Platform


@pytest.fixture
def config():
    cfg = Config()
    cfg.YOUTUBE_CHANNEL_ID = "UC_test_channel"
    cfg.ANALYTICS_LOOKBACK_DAYS = 30
    return cfg


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_youtube():
    return MagicMock()


@pytest.fixture
def agent(config, mock_llm, mock_youtube):
    return TrackingAgent(config=config, llm=mock_llm, youtube=mock_youtube)


class TestFetchYouTubeChannelMetrics:
    def test_returns_channel_metrics(self, agent, mock_youtube):
        mock_youtube.get_channel_analytics.return_value = {
            "viewCount": "1500000",
            "subscriberCount": "25000",
        }
        metrics = agent.fetch_youtube_channel_metrics()
        assert isinstance(metrics, ChannelMetrics)
        assert metrics.total_views == 1500000
        assert metrics.total_subscribers == 25000
        assert metrics.platform == Platform.YOUTUBE

    def test_handles_api_error(self, agent, mock_youtube):
        mock_youtube.get_channel_analytics.side_effect = Exception("API error")
        metrics = agent.fetch_youtube_channel_metrics()
        assert metrics.total_views == 0
        assert metrics.total_subscribers == 0


class TestFetchVideoMetrics:
    def test_returns_video_metrics(self, agent, mock_youtube):
        mock_youtube.get_video_stats.return_value = {
            "statistics": {
                "viewCount": "50000",
                "likeCount": "2000",
                "commentCount": "300",
            },
            "snippet": {
                "title": "AI Tools Guide",
                "publishedAt": "2025-01-15T10:00:00Z",
            },
        }
        metrics = agent.fetch_video_metrics("vid123")
        assert metrics.video_id == "vid123"
        assert metrics.views == 50000
        assert metrics.likes == 2000
        assert metrics.title == "AI Tools Guide"

    def test_handles_api_error(self, agent, mock_youtube):
        mock_youtube.get_video_stats.side_effect = Exception("Not found")
        metrics = agent.fetch_video_metrics("missing_id")
        assert metrics.views == 0
        assert metrics.title == ""


class TestExtractContentPatterns:
    def test_returns_patterns_from_top_videos(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            {
                "pattern_type": "title_format",
                "description": "Listicle titles outperform",
                "examples": ["5 AI Tools", "10 Finance Tips"],
                "avg_ctr_percent": 8.5,
                "avg_views": 200000,
                "confidence": 0.9,
            }
        ]
        videos = [
            VideoMetrics(video_id="v1", platform=Platform.YOUTUBE, title="5 AI Tools", views=200000),
            VideoMetrics(video_id="v2", platform=Platform.YOUTUBE, title="10 Finance Tips", views=180000),
        ]
        patterns = agent.extract_content_patterns(videos)
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "title_format"
        assert patterns[0].confidence == 0.9

    def test_returns_empty_list_for_no_videos(self, agent):
        patterns = agent.extract_content_patterns([])
        assert patterns == []

    def test_handles_dict_wrapped_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "patterns": [
                {
                    "pattern_type": "hook_style",
                    "description": "Question hooks perform well",
                    "examples": [],
                    "avg_ctr_percent": 7.0,
                    "avg_views": 100000,
                    "confidence": 0.8,
                }
            ]
        }
        videos = [
            VideoMetrics(video_id="v1", platform=Platform.YOUTUBE, title="Video", views=100000)
        ]
        patterns = agent.extract_content_patterns(videos)
        assert len(patterns) == 1


class TestGenerateStrategicRecommendations:
    def test_returns_list_of_recommendations(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            "Post 3x per week for faster growth",
            "Focus on Shorts to boost subscriber count",
        ]
        report = PerformanceReport(
            period_start="2025-01-01",
            period_end="2025-01-31",
            top_patterns=[
                ContentPattern(
                    pattern_type="title", description="Listicles work",
                    confidence=0.9
                )
            ],
        )
        recs = agent.generate_strategic_recommendations(report)
        assert len(recs) == 2

    def test_handles_dict_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "recommendations": ["Use trending audio on Shorts"]
        }
        report = PerformanceReport(period_start="2025-01-01", period_end="2025-01-31")
        recs = agent.generate_strategic_recommendations(report)
        assert "Use trending audio on Shorts" in recs


class TestRun:
    def test_run_returns_performance_report(self, agent, mock_youtube, mock_llm):
        mock_youtube.get_channel_analytics.return_value = {
            "viewCount": "500000",
            "subscriberCount": "10000",
        }
        mock_youtube.get_video_stats.return_value = {
            "statistics": {"viewCount": "50000", "likeCount": "1000", "commentCount": "100"},
            "snippet": {"title": "Test Video", "publishedAt": "2025-01-01T00:00:00Z"},
        }
        # extract_content_patterns + generate_strategic_recommendations
        mock_llm.complete_json.side_effect = [
            [],    # patterns
            ["Recommendation 1"],  # recommendations
        ]
        report = agent.run(published_video_ids=["vid1"])
        assert isinstance(report, PerformanceReport)
        assert report.period_start != ""
        assert report.period_end != ""
        assert "Recommendation 1" in report.strategic_recommendations
