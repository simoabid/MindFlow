# tests/test_gemini_client.py
import pytest
from mindflow.gemini_client import GeminiClient

def test_returns_predictions_for_valid_context():
    """Client should return a list of prediction strings."""
    client = GeminiClient(api_key="test-key", model="gemini-2.0-flash")
    predictions = client.get_predictions_sync("The quick brown")
    assert isinstance(predictions, list)

def test_empty_context_returns_empty():
    """Empty context should return no predictions."""
    client = GeminiClient(api_key="test-key")
    predictions = client.get_predictions_sync("")
    assert predictions == []

def test_short_context_returns_empty():
    """Context shorter than threshold should return empty."""
    client = GeminiClient(api_key="test-key")
    predictions = client.get_predictions_sync("ab")  # < 3 chars
    assert predictions == []
