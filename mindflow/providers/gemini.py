# mindflow/providers/gemini.py
"""Gemini-backed prediction provider."""

from __future__ import annotations

from ..config import MindFlowConfig
from ..constants import PROVIDER_GEMINI
from ..gemini_client import GeminiClient
from .base import PredictionProvider


class GeminiProvider(PredictionProvider):
    """Predictions from Google Gemini via :class:`GeminiClient`."""

    name = PROVIDER_GEMINI

    def __init__(self, config: MindFlowConfig):
        self._config = config
        self._client = GeminiClient(
            api_key=config.api_key,
            model=config.model,
            max_predictions=config.max_predictions,
            max_suggestion_words=config.max_suggestion_words,
            min_buffer_length=config.min_buffer_length,
            max_context_length=config.max_context_length,
        )

    def predict(self, context: str) -> list[str]:
        if not self.is_available():
            return []
        return self._client.get_predictions_sync(context)

    def is_available(self) -> bool:
        return bool(self._client.api_key.strip())

    def describe(self) -> str:
        if not self.is_available():
            return f"{self.name} (no API key)"
        return f"{self.name} (model={self._config.model})"
