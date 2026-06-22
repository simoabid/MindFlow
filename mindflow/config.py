# mindflow/config.py
"""Configuration management for MindFlow."""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict

from .constants import (
    DEFAULT_MODEL,
    DEBOUNCE_MS,
    MAX_PREDICTIONS,
    MAX_SUGGESTION_WORDS,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mindflow"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


@dataclass
class MindFlowConfig:
    """MindFlow configuration."""

    api_key: str = ""
    model: str = DEFAULT_MODEL
    enabled: bool = True
    debounce_ms: int = DEBOUNCE_MS
    max_predictions: int = MAX_PREDICTIONS
    max_suggestion_words: int = MAX_SUGGESTION_WORDS
    min_buffer_length: int = 3
    trigger_key: str = "space"  # Trigger prediction after this key
    accept_key: str = "Tab"     # Accept top prediction with this key

    def save(self, path: str | None = None):
        """Save config to JSON file."""
        config_path = Path(path) if path else DEFAULT_CONFIG_FILE
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(asdict(self), f, indent=2)
        logger.info(f"Config saved to {config_path}")

    @classmethod
    def load(cls, path: str | None = None) -> "MindFlowConfig":
        """Load config from JSON file, falling back to defaults."""
        config_path = Path(path) if path else DEFAULT_CONFIG_FILE
        if not config_path.exists():
            logger.info("No config file found, using defaults")
            return cls()

        try:
            with open(config_path) as f:
                data = json.load(f)
            # Filter to only known fields
            valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()
