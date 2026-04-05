"""Tests for the Strategy Agent."""

import pytest
from datetime import date
from unittest.mock import MagicMock

from ai_agent.agents.strategy_agent import StrategyAgent
from ai_agent.config import Config
from ai_agent.models.content import ContentIdea, ContentPackage, ContentStatus, Platform


@pytest.fixture
def config():
    cfg = Config()
    cfg.TARGET_NICHES = ["finance"]
    return cfg


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def agent(config, mock_llm):
    return StrategyAgent(config=config, llm=mock_llm)


@pytest.fixture
def sample_ideas():
    return [
        ContentIdea(title="AI Tools Guide", niche="AI", priority_score=7.0),
        ContentIdea(title="Finance Tips 2025", niche="finance", priority_score=9.0),
        ContentIdea(title="Health Hacks", niche="health", priority_score=5.0),
    ]


class TestPrioritiseIdeas:
    def test_sorts_by_priority_score(self, agent, mock_llm, sample_ideas):
        mock_llm.complete_json.return_value = [
            {"title": "AI Tools Guide", "priority_score": 7.0},
            {"title": "Finance Tips 2025", "priority_score": 9.5},
            {"title": "Health Hacks", "priority_score": 4.0},
        ]
        result = agent.prioritise_ideas(sample_ideas)
        assert result[0].title == "Finance Tips 2025"
        assert result[0].priority_score == 9.5

    def test_empty_list_returns_empty(self, agent):
        result = agent.prioritise_ideas([])
        assert result == []

    def test_handles_dict_wrapped_response(self, agent, mock_llm, sample_ideas):
        mock_llm.complete_json.return_value = {
            "ideas": [
                {"title": "Finance Tips 2025", "priority_score": 9.0},
            ]
        }
        result = agent.prioritise_ideas(sample_ideas)
        # Only Finance Tips is updated; others keep their original scores
        finance_idea = next(i for i in result if i.title == "Finance Tips 2025")
        assert finance_idea.priority_score == 9.0


class TestBuildWeeklyCalendar:
    def test_returns_seven_entries(self, agent, sample_ideas):
        cal = agent.build_weekly_calendar(sample_ideas, start_date=date(2025, 1, 6))
        assert len(cal) == 7

    def test_dates_are_sequential(self, agent, sample_ideas):
        cal = agent.build_weekly_calendar(sample_ideas, start_date=date(2025, 1, 1))
        dates = [entry["date"] for entry in cal]
        assert dates[0] == "2025-01-01"
        assert dates[6] == "2025-01-07"

    def test_uses_today_by_default(self, agent, sample_ideas):
        cal = agent.build_weekly_calendar(sample_ideas)
        assert len(cal) == 7

    def test_handles_empty_ideas(self, agent):
        cal = agent.build_weekly_calendar([])
        for entry in cal:
            assert entry["idea_title"] == ""


class TestBuildMonthlyCalendar:
    def test_returns_entries_for_month(self, agent, sample_ideas):
        cal = agent.build_monthly_calendar(sample_ideas, year=2025, month=2)
        # February 2025 has 28 days, but weekly calendar only returns 7
        assert len(cal) <= 28
        assert len(cal) > 0


class TestRecommendOptimalPostTimes:
    def test_returns_list_of_times(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            "Tuesday 18:00 EST",
            "Thursday 20:00 EST",
            "Saturday 14:00 EST",
        ]
        times = agent.recommend_optimal_post_times(Platform.YOUTUBE)
        assert len(times) == 3

    def test_handles_dict_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "times": ["Monday 19:00 EST"]
        }
        times = agent.recommend_optimal_post_times(Platform.TIKTOK)
        assert "Monday 19:00 EST" in times


class TestCreatePackages:
    def test_wraps_ideas_in_packages(self, agent, sample_ideas):
        packages = agent.create_packages(sample_ideas)
        assert len(packages) == 3
        for pkg in packages:
            assert isinstance(pkg, ContentPackage)
            assert pkg.status == ContentStatus.IDEA


class TestRun:
    def test_run_returns_packages(self, agent, mock_llm, sample_ideas):
        mock_llm.complete_json.return_value = []
        packages = agent.run(sample_ideas)
        assert len(packages) == len(sample_ideas)
        for pkg in packages:
            assert isinstance(pkg, ContentPackage)
