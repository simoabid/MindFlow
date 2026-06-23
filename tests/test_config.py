# tests/test_config.py
from mindflow.config import MindFlowConfig
from mindflow.constants import DEFAULT_MODEL


def test_default_config():
    """Default config should have sensible defaults."""
    config = MindFlowConfig()
    assert config.model == DEFAULT_MODEL
    assert config.api_key == ""
    assert config.enabled is True
    assert config.max_predictions == 6
    assert config.max_suggestion_words == 12


def test_save_and_load(tmp_path):
    """Config should persist to JSON file."""
    config_path = tmp_path / "config.json"
    config = MindFlowConfig(
        api_key="test-key-123",
        model="gemini-1.5-flash",
        max_predictions=8,
        max_suggestion_words=5,
    )
    config.save(str(config_path))

    loaded = MindFlowConfig.load(str(config_path))
    assert loaded.api_key == "test-key-123"
    assert loaded.model == "gemini-1.5-flash"
    assert loaded.max_predictions == 8
    assert loaded.max_suggestion_words == 5


def test_load_nonexistent_returns_defaults():
    """Loading from nonexistent file should return defaults."""
    config = MindFlowConfig.load("/tmp/nonexistent_config.json")
    assert config.model == DEFAULT_MODEL
    assert config.api_key == ""


def test_load_corrupted_json(tmp_path):
    """Loading corrupted JSON should return defaults."""
    config_path = tmp_path / "bad.json"
    config_path.write_text("not valid json{{{")
    config = MindFlowConfig.load(str(config_path))
    assert config.model == DEFAULT_MODEL


def test_env_var_overrides_api_key(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    MindFlowConfig(api_key="from-file").save(str(config_path))
    monkeypatch.setenv("MINDFLOW_API_KEY", "from-env")
    config = MindFlowConfig.load(str(config_path))
    assert config.api_key == "from-env"


def test_gemini_env_var_fallback(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.delenv("MINDFLOW_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-env")
    config = MindFlowConfig.load(str(config_path))
    assert config.api_key == "gemini-env"


def test_validate_clamps_bad_values():
    config = MindFlowConfig(
        max_predictions=0,
        min_buffer_length=-5,
        debounce_ms=-1,
        provider="bogus",
    )
    config.validate()
    assert config.max_predictions >= 1
    assert config.min_buffer_length >= 1
    assert config.debounce_ms >= 0
    assert config.provider == "gemini"  # unknown provider falls back


def test_unknown_keys_are_ignored(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"api_key": "k", "totally_unknown": 1}')
    config = MindFlowConfig.load(str(config_path))
    assert config.api_key == "k"


def test_has_api_key_property():
    assert MindFlowConfig(api_key="  ").has_api_key is False
    assert MindFlowConfig(api_key="key").has_api_key is True


def test_config_override_path_env(tmp_path, monkeypatch):
    config_path = tmp_path / "custom.json"
    MindFlowConfig(max_predictions=7).save(str(config_path))
    monkeypatch.setenv("MINDFLOW_CONFIG", str(config_path))
    config = MindFlowConfig.load()
    assert config.max_predictions == 7
