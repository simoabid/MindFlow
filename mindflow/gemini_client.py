# mindflow/gemini_client.py
"""Gemini API client for text predictions."""

import os
import logging
from google import genai
from google.genai import types

from .constants import (
    DEFAULT_MODEL,
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
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.max_predictions = max(1, int(max_predictions))
        self.max_suggestion_words = max(1, int(max_suggestion_words))
        self._client = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def get_predictions_sync(self, context: str) -> list[str]:
        """Get text predictions for the given context.

        Args:
            context: The text the user has typed so far.

        Returns:
            List of prediction strings (most likely first).
        """
        if not context or len(context.strip()) < MIN_BUFFER_LENGTH:
            return []

        # Trim context to max length
        if len(context) > MAX_CONTEXT_LENGTH:
            context = context[-MAX_CONTEXT_LENGTH:]

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
                    max_output_tokens=50,
                    top_p=0.8,
                ),
            )

            text = (response.text or "").strip()
            if not text:
                return []

            predictions: list[str] = []
            for line in text.split("\n"):
                prediction = self._clean_prediction(line)
                if prediction:
                    predictions.append(prediction)
                if len(predictions) >= self.max_predictions:
                    break

            return predictions

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
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
