# tests/test_predictor.py
from mindflow.predictor import Predictor
from mindflow.providers.base import PredictionProvider


class CountingProvider(PredictionProvider):
    """Test double that records how many times it was asked to predict."""

    name = "counting"

    def __init__(self, result=None):
        self.calls = 0
        self.learned: list[str] = []
        self._result = result if result is not None else ["fox jumped over", "fox ran away"]

    def predict(self, context: str) -> list[str]:
        self.calls += 1
        return list(self._result)

    def is_available(self) -> bool:
        return True

    def learn(self, text: str) -> None:
        self.learned.append(text)


def _predictor(provider, **kwargs):
    return Predictor(provider, min_buffer_length=3, **kwargs)


def test_predictor_caches_results():
    """Same context should return cached results without re-calling the provider."""
    provider = CountingProvider()
    predictor = _predictor(provider)

    result1 = predictor.get_predictions("Hello world this is")
    result2 = predictor.get_predictions("Hello world this is")

    assert result1 == ["fox jumped over", "fox ran away"]
    assert result2 == result1
    assert provider.calls == 1  # second call served from cache


def test_predictor_calls_provider_for_new_context():
    provider = CountingProvider(result=["is a test"])
    predictor = _predictor(provider)

    result = predictor.get_predictions("Hello world this is a new sentence about")
    assert result == ["is a test"]
    assert provider.calls == 1


def test_predictor_handles_empty():
    """Empty / too-short input should return empty list and not call the provider."""
    provider = CountingProvider()
    predictor = _predictor(provider)
    assert predictor.get_predictions("") == []
    assert predictor.get_predictions("ab") == []
    assert provider.calls == 0


def test_predictor_has_predictions():
    provider = CountingProvider(result=["test"])
    predictor = _predictor(provider)
    assert predictor.has_predictions is False
    predictor.get_predictions("Hello world test")
    assert predictor.has_predictions is True


def test_clear_pending_keeps_cache_warm():
    """Dismissing predictions must not wipe the cache (regression test)."""
    provider = CountingProvider()
    predictor = _predictor(provider)

    predictor.get_predictions("Hello world this is")
    predictor.clear_pending()
    assert predictor.has_predictions is False

    predictor.get_predictions("Hello world this is")
    assert provider.calls == 1  # still cached, no new provider call


def test_clear_cache_resets_everything():
    provider = CountingProvider()
    predictor = _predictor(provider)
    predictor.get_predictions("Hello world this is")
    predictor.clear_cache()
    assert predictor.has_predictions is False
    predictor.get_predictions("Hello world this is")
    assert provider.calls == 2  # cache was cleared, provider called again


def test_predictor_learn_delegates_to_provider():
    provider = CountingProvider()
    predictor = _predictor(provider)
    predictor.learn("hello world")
    assert provider.learned == ["hello world"]


def test_from_config_builds_local_provider():
    from mindflow.config import MindFlowConfig

    config = MindFlowConfig(provider="local")
    predictor = Predictor.from_config(config)
    predictions = predictor.get_predictions("Thank you for your ")
    assert isinstance(predictions, list)
    assert predictions  # local provider should produce something from the seed corpus
