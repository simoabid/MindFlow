# mindflow/gemini_client.py
"""Gemini API client for text predictions."""

from __future__ import annotations

import logging
import os

from google import genai
from google.genai import types

from .constants import (
    DEFAULT_MODEL,
    ENV_API_KEY,
    ENV_API_KEY_FALLBACK,
    MAX_CONTEXT_LENGTH,
    MAX_PREDICTIONS,
    MAX_SUGGESTION_WORDS,
    MIN_BUFFER_LENGTH,
)

logger = logging.getLogger(__name__)

PREDICTION_PROMPT = """You are a text autocomplete engine. Given the text the user is currently typing, predict the next few words or short phrase they are likely to type.

Rules:
- Return ONLY the predicted continuation, nothing else
- Keep predictions concise (2-{max_suggestion_words} words each)
- Return up to {max_predictions} different predictions, one per line
- Rank by likelihood (most likely first)
- Do NOT repeat the input text
- Do NOT add quotes, numbers, or bullet points

Current text: {context}"""


class GeminiClient:
    """Synchronous Gemini API client for text predictions."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        max_predictions: int = MAX_PREDICTIONS,
        max_suggestion_words: int = MAX_SUGGESTION_WORDS,
        min_buffer_length: int = MIN_BUFFER_LENGTH,
        max_context_length: int = MAX_CONTEXT_LENGTH,
    ):
        self.api_key: str = (
            api_key or os.environ.get(ENV_API_KEY) or os.environ.get(ENV_API_KEY_FALLBACK) or ""
        )
        self.model = model
        self.max_predictions = max(1, int(max_predictions))
        self.max_suggestion_words = max(1, int(max_suggestion_words))
        self.min_buffer_length = max(1, int(min_buffer_length))
        self.max_context_length = max(16, int(max_context_length))
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _max_output_tokens(self) -> int:
        """Budget enough tokens for the requested predictions (~1.6 tokens/word)."""
        per_line = int(self.max_suggestion_words * 1.6) + 2
        return max(32, per_line * self.max_predictions)

    def get_predictions_sync(self, context: str) -> list[str]:
        """Get text predictions for the given context.

        Args:
            context: The text the user has typed so far.

        Returns:
            List of prediction strings (most likely first).
        """
        if not context or len(context.strip()) < self.min_buffer_length:
            return []

        # Trim context to max length
        if len(context) > self.max_context_length:
            context = context[-self.max_context_length :]

        try:
            prompt = PREDICTION_PROMPT.format(
                max_predictions=self.max_predictions,
                max_suggestion_words=self.max_suggestion_words,
                context=context,
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=self._max_output_tokens(),
                    top_p=0.8,
                ),
            )

            text = (response.text or "").strip()
            if not text:
                return []

            predictions: list[str] = []
            for line in text.split("\n"):
                prediction = self._clean_prediction(line)
                if prediction and prediction not in predictions:
                    predictions.append(prediction)
                if len(predictions) >= self.max_predictions:
                    break

            return predictions

        except Exception as e:
            logger.error("Gemini API error: %s", e)
            return []

    def _clean_prediction(self, prediction: str) -> str:
        """Normalize one model line and enforce the configured word limit."""
        prediction = prediction.strip().strip("\"'")
        if not prediction or prediction.startswith("#"):
            return ""

        prediction = prediction.lstrip("-*•0123456789. )\t").strip()
        words = prediction.split()
        if not words:
            return ""
        return " ".join(words[: self.max_suggestion_words])
