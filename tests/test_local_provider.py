# tests/test_local_provider.py
from mindflow.providers.local import LocalProvider, _tokenize


def test_tokenize_lowercases_and_splits():
    assert _tokenize("Hello, World!") == ["hello", "world"]


def test_predict_next_word_after_space():
    provider = LocalProvider()
    predictions = provider.predict("Thank you for your ")
    assert predictions
    # 'your' is followed by 'email'/'help'/'schedule'/'patience' in the corpus.
    assert all(isinstance(p, str) and p for p in predictions)


def test_predict_completes_partial_word():
    provider = LocalProvider()
    predictions = provider.predict("I am writ")
    assert predictions
    # Should complete the partial token "writ" -> "writing".
    assert any(p.split()[0].startswith("writ") for p in predictions)


def test_predict_respects_max_predictions():
    provider = LocalProvider(max_predictions=2)
    predictions = provider.predict("I ")
    assert len(predictions) <= 2


def test_predict_respects_max_suggestion_words():
    provider = LocalProvider(max_suggestion_words=2)
    predictions = provider.predict("Please let me know if you ")
    assert all(len(p.split()) <= 2 for p in predictions)


def test_empty_context_returns_empty():
    provider = LocalProvider()
    assert provider.predict("") == []
    assert provider.predict("   ") == []


def test_is_available_true_with_seed_corpus():
    assert LocalProvider().is_available() is True


def test_learn_influences_predictions():
    provider = LocalProvider()
    provider.learn("zzzap qqquux frobnicate")
    predictions = provider.predict("zzzap ")
    assert any("qqquux" in p for p in predictions)


def test_history_persists_across_instances(tmp_path):
    history = tmp_path / "history.json"
    p1 = LocalProvider(history_path=history)
    p1.learn("xyzzy plover wibble")
    assert history.exists()

    p2 = LocalProvider(history_path=history)
    predictions = p2.predict("xyzzy ")
    assert any("plover" in pred for pred in predictions)


def test_predictions_are_deduplicated():
    provider = LocalProvider()
    predictions = provider.predict("the ")
    assert len(predictions) == len({p.lower() for p in predictions})
