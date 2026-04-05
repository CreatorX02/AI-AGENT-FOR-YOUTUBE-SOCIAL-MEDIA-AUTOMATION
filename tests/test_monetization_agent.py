"""Tests for the Monetization Agent."""

import pytest
from unittest.mock import MagicMock

from ai_agent.agents.monetization_agent import MonetizationAgent
from ai_agent.config import Config
from ai_agent.models.content import ContentIdea, ContentPackage, MonetizationPlan


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def agent(mock_llm):
    return MonetizationAgent(config=Config(), llm=mock_llm)


@pytest.fixture
def sample_package():
    idea = ContentIdea(
        title="How to Invest Your First $1000", niche="finance", estimated_rpm=12.0
    )
    return ContentPackage(idea=idea)


class TestAnalyseNicheMonetization:
    def test_returns_analysis_dict(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "average_rpm_usd": 15.0,
            "top_ad_keywords": ["best investment 2025", "passive income"],
            "best_affiliate_programs": ["Robinhood", "Acorns"],
            "digital_product_opportunities": ["Investment course", "Budget template"],
            "sponsorship_categories": ["FinTech", "Banking"],
            "estimated_monthly_revenue_per_100k_views_usd": 1200.0,
            "notes": "Finance has one of the highest RPMs on YouTube.",
        }
        result = agent.analyse_niche_monetization("finance")
        assert result["average_rpm_usd"] == 15.0
        assert len(result["top_ad_keywords"]) == 2
        mock_llm.complete_json.assert_called_once()


class TestBuildMonetizationPlan:
    def test_returns_monetization_plan(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "ad_revenue_keywords": ["best brokerage", "index funds explained"],
            "affiliate_suggestions": ["Robinhood", "M1 Finance"],
            "digital_product_ideas": ["Stock Picking Course"],
            "sponsorship_categories": ["FinTech Apps"],
            "estimated_monthly_revenue_usd": 2500.0,
            "notes": "Strong monetisation potential.",
        }
        plan = agent.build_monetization_plan(sample_package)
        assert isinstance(plan, MonetizationPlan)
        assert plan.estimated_monthly_revenue_usd == 2500.0
        assert "Robinhood" in plan.affiliate_suggestions
        assert plan.notes == "Strong monetisation potential."

    def test_handles_missing_keys(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {}
        plan = agent.build_monetization_plan(sample_package)
        assert plan.ad_revenue_keywords == []
        assert plan.estimated_monthly_revenue_usd == 0.0


class TestIdentifyHighRPMKeywords:
    def test_returns_list_of_keywords(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            {"keyword": "best credit card", "estimated_rpm_usd": 18.0, "niche": "finance"},
            {"keyword": "AI stock trading", "estimated_rpm_usd": 14.0, "niche": "AI"},
        ]
        keywords = agent.identify_high_rpm_keywords(["finance", "AI"])
        assert len(keywords) == 2
        assert keywords[0]["estimated_rpm_usd"] == 18.0

    def test_handles_dict_wrapped_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "keywords": [{"keyword": "life insurance", "estimated_rpm_usd": 22.0, "niche": "finance"}]
        }
        keywords = agent.identify_high_rpm_keywords(["finance"])
        assert len(keywords) == 1
        assert keywords[0]["keyword"] == "life insurance"


class TestRun:
    def test_run_attaches_plans_to_packages(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "ad_revenue_keywords": ["keyword1"],
            "affiliate_suggestions": ["affiliate1"],
            "digital_product_ideas": ["product1"],
            "sponsorship_categories": ["category1"],
            "estimated_monthly_revenue_usd": 800.0,
            "notes": "",
        }
        packages = agent.run([sample_package])
        assert packages[0].monetization is not None
        assert packages[0].monetization.estimated_monthly_revenue_usd == 800.0

    def test_run_handles_errors_gracefully(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.side_effect = Exception("LLM error")
        packages = agent.run([sample_package])
        assert packages[0].monetization is None
