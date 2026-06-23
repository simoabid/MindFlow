# tests/test_providers.py
from mindflow.config import MindFlowConfig
from mindflow.providers import (
    FallbackProvider,
    GeminiProvider,
    LocalProvider,
    build_provider,
)
from mindflow.providers.base import PredictionProvider


class StubProvider(PredictionProvider):
    def __init__(self, name, available, result):
        self.name = name
        self._available = available
        self._result = result
        self.learned = []

    def predict(self, context):
        return list(self._result)

    def is_available(self):
        return self._available

    def learn(self, text):
        self.learned.append(text)


def test_build_provider_local():
    provider = build_provider(MindFlowConfig(provider="local"))
    assert isinstance(provider, LocalProvider)


def test_build_provider_gemini_wraps_fallback():
    provider = build_provider(MindFlowConfig(provider="gemini"))
    assert isinstance(provider, FallbackProvider)
    assert isinstance(provider.primary, GeminiProvider)
    assert isinstance(provider.fallback, LocalProvider)


def test_gemini_provider_unavailable_without_key():
    provider = GeminiProvider(MindFlowConfig(provider="gemini", api_key=""))
    assert provider.is_available() is False
    assert provider.predict("hello world") == []


def test_fallback_uses_primary_when_available():
    primary = StubProvider("primary", available=True, result=["from primary"])
    fallback = StubProvider("fallback", available=True, result=["from fallback"])
    fp = FallbackProvider(primary, fallback)
    assert fp.predict("anything") == ["from primary"]


def test_fallback_uses_fallback_when_primary_unavailable():
    primary = StubProvider("primary", available=False, result=["from primary"])
    fallback = StubProvider("fallback", available=True, result=["from fallback"])
    fp = FallbackProvider(primary, fallback)
    assert fp.predict("anything") == ["from fallback"]


def test_fallback_uses_fallback_when_primary_empty():
    primary = StubProvider("primary", available=True, result=[])
    fallback = StubProvider("fallback", available=True, result=["from fallback"])
    fp = FallbackProvider(primary, fallback)
    assert fp.predict("anything") == ["from fallback"]


def test_fallback_learn_propagates_to_both():
    primary = StubProvider("primary", available=True, result=[])
    fallback = StubProvider("fallback", available=True, result=[])
    fp = FallbackProvider(primary, fallback)
    fp.learn("text")
    assert primary.learned == ["text"]
    assert fallback.learned == ["text"]
