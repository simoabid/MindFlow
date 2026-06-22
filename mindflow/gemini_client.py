# mindflow/gemini_client.py
"""Gemini API client for text predictions."""

import os
import logging
from google import genai
from google.genai import types

from .constants import DEFAULT_MODEL, MAX_PREDICTIONS, MAX_CONTEXT_LENGTH, MIN_BUFFER_LENGTH

logger = logging.getLogger(__name__)

PREDICTION_PROMPT = """You are a text autocomplete engine. Given the text the user is currently typing, predict the next few words or short phrase they are likely to type. 

Rules:
- Return ONLY the predicted continuation, nothing else
- Keep predictions concise (2-8 words each)
- Return up to {max_predictions} different predictions, one per line
- Rank by likelihood (most likely first)
- Do NOT repeat the input text
- Do NOT add quotes, numbers, or bullet points

Current text: {context}"""


class GeminiClient:
    """Synchronous Gemini API client for text predictions."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
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
                max_predictions=MAX_PREDICTIONS,
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

            text = response.text.strip()
            if not text:
                return []

            predictions = [
                line.strip()
                for line in text.split("\n")
                if line.strip() and not line.strip().startswith(("#", "-"))
            ][:MAX_PREDICTIONS]

            return predictions

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return []
