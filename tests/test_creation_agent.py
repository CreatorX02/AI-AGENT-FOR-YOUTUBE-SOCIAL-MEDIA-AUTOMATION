"""Tests for the Creation Agent."""

import pytest
from unittest.mock import MagicMock

from ai_agent.agents.creation_agent import CreationAgent
from ai_agent.config import Config
from ai_agent.models.content import (
    ContentIdea,
    ContentPackage,
    Platform,
    Script,
    ThumbnailConcept,
    VisualDirection,
)


@pytest.fixture
def mock_llm():
    return MagicMock()


@pytest.fixture
def agent(mock_llm):
    return CreationAgent(config=Config(), llm=mock_llm)


@pytest.fixture
def sample_package():
    idea = ContentIdea(
        title="5 AI Tools That Changed My Life",
        niche="AI",
        hook="You're wasting hours every day on tasks AI can do instantly.",
    )
    return ContentPackage(idea=idea)


class TestGenerateScript:
    def test_returns_script_object(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "hook": "Stop scrolling. These AI tools will change your life.",
            "body": "In this video we cover tools 1 through 5...",
            "call_to_action": "Subscribe for weekly AI tips.",
            "estimated_duration_seconds": 600,
        }
        script = agent.generate_script(sample_package)
        assert isinstance(script, Script)
        assert script.title == sample_package.idea.title
        assert script.estimated_duration_seconds == 600
        assert script.platform == Platform.YOUTUBE

    def test_uses_platform_specific_limits(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "hook": "Quick hook",
            "body": "Short body",
            "call_to_action": "Follow me!",
            "estimated_duration_seconds": 45,
        }
        script = agent.generate_script(sample_package, platform=Platform.YOUTUBE_SHORTS)
        assert script.platform == Platform.YOUTUBE_SHORTS
        # Verify the platform was included in the LLM prompt
        call_args = mock_llm.complete_json.call_args[0][1]
        assert "youtube_shorts" in call_args

    def test_defaults_to_youtube_platform(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "hook": "h", "body": "b", "call_to_action": "cta",
            "estimated_duration_seconds": 300,
        }
        script = agent.generate_script(sample_package)
        assert script.platform == Platform.YOUTUBE


class TestGenerateVisualDirection:
    def test_returns_visual_direction(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            {"timestamp": "0:00", "description": "Intro shot", "b_roll": "City timelapse"},
            {"timestamp": "0:30", "description": "Screen recording", "b_roll": ""},
        ]
        script = Script(title="Test", hook="hook", body="body", call_to_action="cta")
        vd = agent.generate_visual_direction(script)
        assert isinstance(vd, VisualDirection)
        assert len(vd.scenes) == 2
        assert vd.scenes[0]["timestamp"] == "0:00"

    def test_handles_dict_wrapped_response(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "scenes": [
                {"timestamp": "0:00", "description": "Opening", "b_roll": "Sunrise"}
            ]
        }
        script = Script(title="T", hook="h", body="b", call_to_action="c")
        vd = agent.generate_visual_direction(script)
        assert len(vd.scenes) == 1

    def test_skips_non_dict_scenes(self, agent, mock_llm):
        mock_llm.complete_json.return_value = [
            "not a dict",
            {"timestamp": "0:00", "description": "Valid scene", "b_roll": ""},
        ]
        script = Script(title="T", hook="h", body="b", call_to_action="c")
        vd = agent.generate_visual_direction(script)
        assert len(vd.scenes) == 1


class TestGenerateThumbnailConcept:
    def test_returns_thumbnail(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "headline_text": "These AI Tools Will Shock You",
            "background_description": "Dark gradient with glowing tech",
            "emotion": "shock",
            "color_scheme": "dark blue and gold",
            "notes": "Include robot graphic",
        }
        thumb = agent.generate_thumbnail_concept(sample_package)
        assert isinstance(thumb, ThumbnailConcept)
        assert thumb.emotion == "shock"
        assert thumb.color_scheme == "dark blue and gold"

    def test_default_emotion_fallback(self, agent, mock_llm, sample_package):
        mock_llm.complete_json.return_value = {
            "headline_text": "Amazing AI",
            "background_description": "Simple background",
        }
        thumb = agent.generate_thumbnail_concept(sample_package)
        assert thumb.emotion == "curiosity"


class TestRecommendTools:
    def test_returns_tools_dict(self, agent, mock_llm):
        mock_llm.complete_json.return_value = {
            "voiceover_tools": ["ElevenLabs", "Murf"],
            "editing_tools": ["CapCut", "Runway"],
            "tips": ["Use 48kHz audio", "Export in H.264"],
        }
        result = agent.recommend_tools(Platform.TIKTOK)
        assert "voiceover_tools" in result
        assert "CapCut" in result["editing_tools"]


class TestRun:
    def test_run_populates_all_fields(self, agent, mock_llm):
        mock_llm.complete_json.side_effect = [
            # Script
            {"hook": "h", "body": "b", "call_to_action": "cta", "estimated_duration_seconds": 300},
            # Visual direction
            [{"timestamp": "0:00", "description": "Scene 1", "b_roll": ""}],
            # Thumbnail
            {"headline_text": "Wow", "background_description": "Bg", "emotion": "awe",
             "color_scheme": "red", "notes": ""},
        ]
        idea = ContentIdea(title="Test Video", niche="tech", hook="Test hook")
        pkg = ContentPackage(idea=idea)
        result = agent.run([pkg])
        assert result[0].script is not None
        assert result[0].visual_direction is not None
        assert result[0].thumbnail is not None

    def test_run_handles_errors_gracefully(self, agent, mock_llm):
        mock_llm.complete_json.side_effect = Exception("LLM error")
        idea = ContentIdea(title="Error Video", niche="tech")
        pkg = ContentPackage(idea=idea)
        result = agent.run([pkg])
        # Should not raise, just log the error
        assert result[0].script is None
