# tests/test_config.py
import pytest
import json
from pathlib import Path
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
