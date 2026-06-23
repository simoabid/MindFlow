# mindflow/providers/__init__.py
"""Pluggable prediction backends for MindFlow."""

from __future__ import annotations

import logging
from pathlib import Path

from ..config import MindFlowConfig
from ..constants import PROVIDER_GEMINI, PROVIDER_LOCAL
from .base import PredictionProvider
from .gemini import GeminiProvider
from .local import LocalProvider

logger = logging.getLogger(__name__)

__all__ = [
    "FallbackProvider",
    "GeminiProvider",
    "LocalProvider",
    "PredictionProvider",
    "build_provider",
]


class FallbackProvider(PredictionProvider):
    """Try a primary provider, then fall back to a secondary one.

    The fallback fires both when the primary is unavailable (e.g. Gemini has no
    API key or the network is down) and when it simply returns no predictions.
    """

    name = "fallback"

    def __init__(self, primary: PredictionProvider, fallback: PredictionProvider):
        self.primary = primary
        self.fallback = fallback

    def predict(self, context: str) -> list[str]:
        if self.primary.is_available():
            try:
                predictions = self.primary.predict(context)
            except Exception as e:  # defensive: never let a provider break typing
                logger.warning("Primary provider %r failed: %s", self.primary.name, e)
                predictions = []
            if predictions:
                return predictions
        try:
            return self.fallback.predict(context)
        except Exception as e:  # defensive: a misbehaving fallback must not break typing
            logger.warning("Fallback provider %r failed: %s", self.fallback.name, e)
            return []

    def is_available(self) -> bool:
        return self.primary.is_available() or self.fallback.is_available()

    def learn(self, text: str) -> None:
        self.primary.learn(text)
        self.fallback.learn(text)

    def describe(self) -> str:
        return f"{self.primary.describe()} -> {self.fallback.describe()}"


def build_provider(
    config: MindFlowConfig, history_path: str | Path | None = None
) -> PredictionProvider:
    """Construct the configured provider, wiring an offline fallback for Gemini."""
    local = LocalProvider(
        max_predictions=config.max_predictions,
        max_suggestion_words=config.max_suggestion_words,
        history_path=history_path,
    )

    if config.provider == PROVIDER_LOCAL:
        return local

    if config.provider == PROVIDER_GEMINI:
        gemini = GeminiProvider(config)
        # When Gemini can't serve (no key/offline), keep working locally.
        return FallbackProvider(primary=gemini, fallback=local)

    logger.warning("Unknown provider %r; using local", config.provider)
    return local
