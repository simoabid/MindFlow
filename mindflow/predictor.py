# mindflow/predictor.py
"""Prediction manager with caching and context tracking."""

import time
import logging

from .gemini_client import GeminiClient
from .constants import DEBOUNCE_MS, MIN_BUFFER_LENGTH

logger = logging.getLogger(__name__)


class Predictor:
    """Manages predictions with caching and debouncing."""

    def __init__(self, api_key: str = "", model: str = "gemini-2.0-flash"):
        self.client = GeminiClient(api_key=api_key, model=model)
        self._cache: dict[str, list[str]] = {}
        self._last_request_time: float = 0
        self._last_context: str = ""
        self._pending_predictions: list[str] = []

    def get_predictions(self, context: str) -> list[str]:
        """Get predictions for the current context.

        Uses caching and debouncing to minimize API calls.
        """
        if not context or len(context.strip()) < MIN_BUFFER_LENGTH:
            self._pending_predictions = []
            return []

        # Check cache first
        cache_key = context.strip().lower()
        if cache_key in self._cache:
            self._pending_predictions = self._cache[cache_key]
            return self._pending_predictions

        # Debounce: only make API call if enough time has passed
        now = time.time() * 1000  # ms
        if (now - self._last_request_time) < DEBOUNCE_MS:
            return self._pending_predictions

        self._last_request_time = now
        self._last_context = context

        # Call Gemini
        predictions = self.client.get_predictions_sync(context)
        self._cache[cache_key] = predictions
        self._pending_predictions = predictions

        logger.debug(f"Predictions for '{context[-30:]}': {predictions}")
        return predictions

    def get_pending(self) -> list[str]:
        """Get the last computed predictions without triggering a new call."""
        return self._pending_predictions

    def clear_cache(self):
        """Clear the prediction cache."""
        self._cache.clear()
        self._pending_predictions = []

    @property
    def has_predictions(self) -> bool:
        """Whether there are pending predictions available."""
        return len(self._pending_predictions) > 0
