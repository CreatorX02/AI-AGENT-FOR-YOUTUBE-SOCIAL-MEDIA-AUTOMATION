"""Tests for the SEO Agent."""

import pytest
from unittest.mock import MagicMock

from ai_agent.agents.seo_agent import SEOAgent
from ai_agent.config import Config
from ai_agent.models.content import (
    ContentIdea,
    ContentPackage,
    Platform,
    Script,
    SEOPackage,
)


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def agent(mock_llm):
    return SEOAgent(config=Config(), llm=mock_llm)


@pytest.fixture
def sample_package():
    idea = ContentIdea(title="AI Tools for Beginners", niche="AI", hook="Stop wasting time")
    pkg = ContentPackage(idea=idea)
    pkg.script = Script(
        title=idea.title,
        hook=idea.hook,
        body="In this video we cover 5 essential AI tools...",
        call_to_action="Subscribe for more AI tips.",
        estimated_duration_seconds=480,
    )
    return pkg


class TestOptimiseTitle:
    def test_returns_optimised_title(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {"title": "5 AI Tools That Will Save You 10 Hours/Week"}
        result = agent.optimise_title("AI Tools for Beginners", "AI")
        assert result == "5 AI Tools That Will Save You 10 Hours/Week"

    def test_falls_back_to_original_on_missing_key(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {}
        result = agent.optimise_title("Original Title", "tech")
        assert result == "Original Title"


class TestGenerateDescription:
    def test_returns_description_string(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "description": "In this video, we explore the best AI tools..."
        }
        result = agent.generate_description("AI Tools 2025", "Hook text", "AI")
        assert "AI tools" in result

    def test_empty_description_fallback(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {}
        result = agent.generate_description("Title", "Excerpt", "niche")
        assert result == ""


class TestGenerateTags:
    def test_returns_list_of_tags(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            "ai tools", "artificial intelligence", "chatgpt", "productivity"
        ]
        tags = agent.generate_tags("AI Tools 2025", "AI", count=4)
        assert len(tags) == 4
        assert "ai tools" in tags

    def test_handles_dict_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {"tags": ["finance", "investing"]}
        tags = agent.generate_tags("Finance Tips", "finance")
        assert "finance" in tags


class TestGenerateHashtags:
    def test_returns_list_without_hash_symbol(self, agent, mock_llm):
        mock_llm.complete_json.return_value = ["AITools", "Tech2025", "Productivity"]
        hashtags = agent.generate_hashtags("AI Tools", Platform.TIKTOK, count=3)
        assert all(not h.startswith("#") for h in hashtags)

    def test_handles_dict_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {"hashtags": ["Finance", "Money"]}
        hashtags = agent.generate_hashtags("Finance", Platform.INSTAGRAM_REELS)
        assert "Finance" in hashtags


class TestBuildSEOPackage:
    def test_returns_seo_package(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.side_effect = [
            # optimise_title
            {"title": "5 AI Tools That Will Change Your Life in 2025"},
            # generate_description
            {"description": "Discover the top AI tools that productivity experts use..."},
            # generate_tags
            ["ai tools", "chatgpt", "productivity", "technology"],
            # generate_hashtags
            ["AITools", "Tech", "Productivity"],
        ]
        seo = agent.build_seo_package(sample_package)
        assert isinstance(seo, SEOPackage)
        assert seo.title == "5 AI Tools That Will Change Your Life in 2025"
        assert len(seo.tags) == 4
        assert len(seo.hashtags) == 3


class TestRun:
    def test_run_attaches_seo_to_packages(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.side_effect = [
            {"title": "Optimised Title"},
            {"description": "SEO Description"},
            ["tag1", "tag2"],
            ["hashtag1"],
        ]
        packages = agent.run([sample_package])
        assert packages[0].seo is not None
        assert packages[0].seo.title == "Optimised Title"
        assert packages[0].idea.title == "Optimised Title"

    def test_run_handles_errors_gracefully(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.side_effect = Exception("LLM unavailable")
        packages = agent.run([sample_package])
        assert packages[0].seo is None
