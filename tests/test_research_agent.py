"""Tests for the Research Agent."""

import pytest
from unittest.mock import MagicMock, patch

from ai_agent.agents.research_agent import ResearchAgent
from ai_agent.config import Config
from ai_agent.models.content import ContentIdea, Platform, TrendSignal


@pytest.fixture
def config():
    cfg = Config()
    cfg.TARGET_NICHES = ["finance", "AI"]
    return cfg


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def mock_youtube():
    return MagicMock()


@pytest.fixture
def agent(config, mock_llm, mock_youtube):
    return ResearchAgent(config=config, llm=mock_llm, youtube=mock_youtube)


class TestFetchTrendSignals:
    def test_returns_signals_from_youtube(self, agent, mock_youtube):
        mock_youtube.search_trending.return_value = [
            {
                "id": {"videoId": "vid1"},
                "snippet": {"title": "Top 5 AI Tools 2025"},
            },
            {
                "id": {"videoId": "vid2"},
                "snippet": {"title": "How I Made $10k With AI"},
            },
        ]
        signals = agent.fetch_trend_signals("AI")
        assert len(signals) == 2
        assert signals[0].topic == "Top 5 AI Tools 2025"
        assert signals[0].platform == Platform.YOUTUBE
        assert "vid1" in signals[0].source_url

    def test_handles_youtube_api_error(self, agent, mock_youtube):
        mock_youtube.search_trending.side_effect = Exception("API error")
        signals = agent.fetch_trend_signals("finance")
        assert signals == []

    def test_empty_results(self, agent, mock_youtube):
        mock_youtube.search_trending.return_value = []
        signals = agent.fetch_trend_signals("health")
        assert signals == []


class TestAnalyseNiche:
    def test_returns_llm_data(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "competition_level": "low",
            "rpm_potential": "high",
            "estimated_monthly_searches": 500000,
            "top_content_patterns": ["listicles", "tutorials"],
            "underserved_subtopics": ["DeFi for beginners"],
        }
        result = agent.analyze_niche("finance")
        assert result["competition_level"] == "low"
        assert result["rpm_potential"] == "high"
        mock_llm.complete_json.assert_called_once()


class TestGenerateContentIdeas:
    def test_generates_ideas(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            {
                "title": "5 AI Tools That Changed My Life",
                "hook": "Most people don't know about these AI tools...",
                "estimated_rpm": 7.5,
                "priority_score": 8.2,
            },
            {
                "title": "How to Use ChatGPT to Make Money",
                "hook": "I made $5000 in one week using this AI trick...",
                "estimated_rpm": 9.0,
                "priority_score": 9.1,
            },
        ]
        signals = [TrendSignal(topic="AI Tools", platform=Platform.YOUTUBE)]
        ideas = agent.generate_content_ideas("AI", signals, count=2)
        assert len(ideas) == 2
        assert ideas[0].title == "5 AI Tools That Changed My Life"
        assert ideas[0].estimated_rpm == 7.5
        assert ideas[1].priority_score == 9.1

    def test_handles_dict_wrapped_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "ideas": [
                {
                    "title": "Finance Tips",
                    "hook": "Save more money",
                    "estimated_rpm": 5.0,
                    "priority_score": 6.0,
                }
            ]
        }
        signals = []
        ideas = agent.generate_content_ideas("finance", signals, count=1)
        assert len(ideas) == 1
        assert ideas[0].title == "Finance Tips"

    def test_skips_non_dict_items(self, agent, mock_llm):
        mock_llm.complete_json.return_value = ["invalid", None, {"title": "Valid", "hook": "", "estimated_rpm": 1.0, "priority_score": 1.0}]
        ideas = agent.generate_content_ideas("tech", [], count=3)
        assert len(ideas) == 1
        assert ideas[0].title == "Valid"


class TestIdentifyContentGaps:
    def test_returns_list(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            {
                "niche": "finance",
                "gap_topic": "Crypto for seniors",
                "reason": "Aging population underserved",
                "opportunity_score": 8.0,
            }
        ]
        gaps = agent.identify_content_gaps(["finance", "AI"])
        assert len(gaps) == 1
        assert gaps[0]["gap_topic"] == "Crypto for seniors"


class TestRunCycle:
    def test_run_aggregates_all_niches(self, agent, mock_llm, mock_youtube):
        mock_youtube.search_trending.return_value = []
        mock_llm.complete_json.return_value = [
            {
                "title": "Finance Video",
                "hook": "Hook",
                "estimated_rpm": 5.0,
                "priority_score": 7.0,
            }
        ]
        ideas = agent.run()
        # 2 niches (finance, AI), each returns 1 idea
        assert len(ideas) == 2
        # Ideas sorted by priority_score descending
        for i in range(len(ideas) - 1):
            assert ideas[i].priority_score >= ideas[i + 1].priority_score
