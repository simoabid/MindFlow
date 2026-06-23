# mindflow/predictor.py
"""Prediction manager: provider + bounded cache."""

from __future__ import annotations

import logging
from pathlib import Path

from .cache import TTLCache
from .config import MindFlowConfig
from .constants import (
    CACHE_MAX_ENTRIES,
    CACHE_TTL_SECONDS,
    MIN_BUFFER_LENGTH,
)
from .providers import PredictionProvider, build_provider

logger = logging.getLogger(__name__)


class Predictor:
    """Turns typing context into predictions, caching results per context.

    Debouncing is the caller's responsibility (the IBus engine schedules calls
    on a timer); this class focuses on caching and delegating to a provider.
    """

    def __init__(
        self,
        provider: PredictionProvider,
        *,
        min_buffer_length: int = MIN_BUFFER_LENGTH,
        cache_max_entries: int = CACHE_MAX_ENTRIES,
        cache_ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        self.provider = provider
        self.min_buffer_length = max(1, int(min_buffer_length))
        self._cache = TTLCache(max_entries=cache_max_entries, ttl_seconds=cache_ttl_seconds)
        self._pending_predictions: list[str] = []

    @classmethod
    def from_config(
        cls, config: MindFlowConfig, history_path: str | Path | None = None
    ) -> Predictor:
        """Build a predictor (and its provider) from a config object."""
        return cls(
            provider=build_provider(config, history_path=history_path),
            min_buffer_length=config.min_buffer_length,
            cache_max_entries=config.cache_max_entries,
            cache_ttl_seconds=config.cache_ttl_seconds,
        )

    def get_predictions(self, context: str) -> list[str]:
        """Get predictions for the current context, using the cache when fresh."""
        if not context or len(context.strip()) < self.min_buffer_length:
            self._pending_predictions = []
            return []

        # Case-sensitive key: providers may predict differently for "Python" vs
        # "python", so don't let case variants collide on the same cache entry.
        cache_key = context.strip()
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._pending_predictions = cached
            return cached

        predictions = self.provider.predict(context)
        self._cache.set(cache_key, predictions)
        self._pending_predictions = predictions
        logger.debug("Predictions for '%s': %s", context[-30:], predictions)
        return predictions

    def learn(self, text: str) -> None:
        """Feed accepted text back to the provider so it can adapt."""
        self.provider.learn(text)

    def get_pending(self) -> list[str]:
        """Get the last computed predictions without triggering a new call."""
        return self._pending_predictions

    def clear_pending(self) -> None:
        """Drop the currently displayed predictions (keeps the cache warm)."""
        self._pending_predictions = []

    def clear_cache(self) -> None:
        """Clear the prediction cache and pending predictions."""
        self._cache.clear()
        self._pending_predictions = []

    @property
    def cache_stats(self) -> dict[str, int]:
        return {
            "size": len(self._cache),
            "hits": self._cache.hits,
            "misses": self._cache.misses,
        }

    @property
    def has_predictions(self) -> bool:
        """Whether there are pending predictions available."""
        return len(self._pending_predictions) > 0
