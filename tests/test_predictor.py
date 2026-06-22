# tests/test_predictor.py
import pytest
from unittest.mock import patch, MagicMock
from mindflow.predictor import Predictor

def test_predictor_caches_results():
    """Same context should return cached results without API call."""
    with patch("mindflow.predictor.GeminiClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_predictions_sync.return_value = ["fox jumped over", "fox ran away"]
        
        predictor = Predictor(api_key="test-key")
        result1 = predictor.get_predictions("Hello world this is")
        result2 = predictor.get_predictions("Hello world this is")
        
        assert result1 == ["fox jumped over", "fox ran away"]
        assert result2 == ["fox jumped over", "fox ran away"]
        # API should only be called once (second is cached)
        assert mock_instance.get_predictions_sync.call_count == 1

def test_predictor_clears_on_new_input():
    """Predictions should update when context changes significantly."""
    with patch("mindflow.predictor.GeminiClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.get_predictions_sync.return_value = ["is a test"]
        
        predictor = Predictor(api_key="test-key")
        # Reset call count after any init calls
        mock_instance.get_predictions_sync.reset_mock()
        
        result = predictor.get_predictions("Hello world this is a new sentence about")
        assert result == ["is a test"]
        assert mock_instance.get_predictions_sync.call_count == 1

def test_predictor_handles_empty():
    """Empty input should return empty list."""
    predictor = Predictor(api_key="test-key")
    assert predictor.get_predictions("") == []

def test_predictor_has_predictions():
    """has_predictions property should reflect state."""
    predictor = Predictor(api_key="test-key")
    assert predictor.has_predictions is False
    
    with patch.object(predictor.client, "get_predictions_sync", return_value=["test"]):
        predictor.get_predictions("Hello world test")
        assert predictor.has_predictions is True

def test_predictor_clear_cache():
    """clear_cache should reset everything."""
    predictor = Predictor(api_key="test-key")
    predictor._cache["test"] = ["cached"]
    predictor._pending_predictions = ["pending"]
    
    predictor.clear_cache()
    assert predictor._cache == {}
    assert predictor._pending_predictions == []


def test_predictor_passes_display_settings_to_client():
    """Predictor should pass suggestion count and length settings to GeminiClient."""
    with patch("mindflow.predictor.GeminiClient") as MockClient:
        Predictor(
            api_key="test-key",
            model="test-model",
            max_predictions=6,
            max_suggestion_words=12,
        )

        MockClient.assert_called_once_with(
            api_key="test-key",
            model="test-model",
            max_predictions=6,
            max_suggestion_words=12,
        )
