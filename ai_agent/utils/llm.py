"""LLM client wrapper (OpenAI)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from ai_agent.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Thin wrapper around the OpenAI Chat Completions API."""

    def __init__(self, config: Optional[Config] = None) -> None:
        self._config = config or Config()
        self._client: Any = None  # lazy init to avoid import errors when key absent

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI  # type: ignore

                self._client = OpenAI(api_key=self._config.OPENAI_API_KEY)
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "openai package is required. Run: pip install openai"
                ) from exc
        return self._client

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Return the assistant's text response."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Return a parsed JSON dict from the LLM response.

        The system prompt should instruct the model to respond with valid JSON.
        """
        raw = self.complete(
            system_prompt=system_prompt + "\n\nRespond ONLY with valid JSON.",
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON response; returning raw string.")
            return {"raw": raw}
