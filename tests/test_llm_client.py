"""Tests for the LLM client utility."""

import json
import pytest
from unittest.mock import MagicMock, patch

from ai_agent.utils.llm import LLMClient
from ai_agent.config import Config


@pytest.fixture
def config():
    cfg = Config()
    cfg.OPENAI_API_KEY = "test-key"
    cfg.OPENAI_MODEL = "gpt-4o"
    return cfg


@pytest.fixture
def client(config):
    return LLMClient(config=config)


class TestComplete:
    def test_returns_text_response(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello from GPT"))]
        )
        client._client = mock_openai
        result = client.complete("system", "user prompt")
        assert result == "Hello from GPT"

    def test_passes_correct_model(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="ok"))]
        )
        client._client = mock_openai
        client.complete("sys", "user")
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"

    def test_handles_none_content(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=None))]
        )
        client._client = mock_openai
        result = client.complete("sys", "user")
        assert result == ""


class TestCompleteJSON:
    def test_parses_valid_json(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"key": "value"}'))]
        )
        client._client = mock_openai
        result = client.complete_json("sys", "user")
        assert result == {"key": "value"}

    def test_strips_markdown_code_fences(self, client):
        raw = "```json\n{\"title\": \"AI Video\"}\n```"
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=raw))]
        )
        client._client = mock_openai
        result = client.complete_json("sys", "user")
        assert result["title"] == "AI Video"

    def test_strips_code_fences_without_json_label(self, client):
        raw = "```\n[\"item1\", \"item2\"]\n```"
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=raw))]
        )
        client._client = mock_openai
        result = client.complete_json("sys", "user")
        assert result == ["item1", "item2"]

    def test_returns_raw_on_invalid_json(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="not json at all"))]
        )
        client._client = mock_openai
        result = client.complete_json("sys", "user")
        assert "raw" in result
        assert result["raw"] == "not json at all"

    def test_parses_json_array(self, client):
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='["a", "b", "c"]'))]
        )
        client._client = mock_openai
        result = client.complete_json("sys", "user")
        assert result == ["a", "b", "c"]
