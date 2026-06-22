# tests/test_gemini_client.py
import pytest
from unittest.mock import patch, MagicMock
from mindflow.gemini_client import GeminiClient


def _make_mock_response(text: str | None):
    """Create a mock response object with the given text."""
    response = MagicMock()
    response.text = text
    return response


@patch("mindflow.gemini_client.genai.Client")
def test_returns_predictions_for_valid_context(mock_genai_client_cls):
    """Client should return a list of prediction strings from the API."""
    mock_client = MagicMock()
    mock_genai_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response(
        "jumped over the lazy dog\nran across the field\n"
    )

    client = GeminiClient(api_key="test-key", model="gemini-2.0-flash")
    predictions = client.get_predictions_sync("The quick brown fox")

    assert isinstance(predictions, list)
    assert len(predictions) == 2
    assert "jumped over the lazy dog" in predictions
    assert "ran across the field" in predictions


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


@patch("mindflow.gemini_client.genai.Client")
def test_api_error_returns_empty(mock_genai_client_cls):
    """API errors should be caught and return empty list."""
    mock_client = MagicMock()
    mock_genai_client_cls.return_value = mock_client
    mock_client.models.generate_content.side_effect = RuntimeError("API unavailable")

    client = GeminiClient(api_key="test-key")
    predictions = client.get_predictions_sync("The quick brown fox")

    assert predictions == []


@patch("mindflow.gemini_client.genai.Client")
def test_none_response_text_returns_empty(mock_genai_client_cls):
    """None response.text (e.g. safety filter block) should return empty, not crash."""
    mock_client = MagicMock()
    mock_genai_client_cls.return_value = mock_client
    mock_client.models.generate_content.return_value = _make_mock_response(None)

    client = GeminiClient(api_key="test-key")
    predictions = client.get_predictions_sync("The quick brown fox")

    assert predictions == []
