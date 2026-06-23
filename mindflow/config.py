# mindflow/config.py
"""Configuration management for MindFlow."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .constants import (
    CACHE_MAX_ENTRIES,
    CACHE_TTL_SECONDS,
    CONFIG_FILE,
    DEBOUNCE_MS,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ENV_API_KEY,
    ENV_API_KEY_FALLBACK,
    ENV_CONFIG_FILE,
    MAX_PREDICTIONS,
    MAX_SUGGESTION_WORDS,
    MIN_BUFFER_LENGTH,
    PROVIDER_GEMINI,
    PROVIDER_LOCAL,
)

logger = logging.getLogger(__name__)

# Kept for backwards compatibility with code/tests importing these names.
DEFAULT_CONFIG_DIR = CONFIG_FILE.parent
DEFAULT_CONFIG_FILE = CONFIG_FILE

VALID_PROVIDERS = (PROVIDER_GEMINI, PROVIDER_LOCAL)


@dataclass
class MindFlowConfig:
    """MindFlow configuration."""

    api_key: str = ""
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    enabled: bool = True
    debounce_ms: int = DEBOUNCE_MS
    max_predictions: int = MAX_PREDICTIONS
    max_suggestion_words: int = MAX_SUGGESTION_WORDS
    min_buffer_length: int = MIN_BUFFER_LENGTH
    max_context_length: int = 200
    cache_max_entries: int = CACHE_MAX_ENTRIES
    cache_ttl_seconds: int = CACHE_TTL_SECONDS
    trigger_key: str = "space"  # Trigger prediction after this key
    accept_key: str = "Tab"  # Accept top prediction with this key

    # Privacy
    disable_in_password_fields: bool = True
    blocklist_apps: list[str] = field(default_factory=list)

    # Telemetry (fully local, never leaves the machine)
    stats_enabled: bool = True

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        """Save config to JSON file."""
        config_path = Path(path) if path else _config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        logger.info("Config saved to %s", config_path)

    @classmethod
    def load(cls, path: str | os.PathLike[str] | None = None) -> MindFlowConfig:
        """Load config from JSON file, applying env overrides and validation."""
        config_path = Path(path) if path else _config_path()
        config = cls()

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)
                valid_keys = {f.name for f in fields(cls)}
                filtered = {k: v for k, v in data.items() if k in valid_keys}
                config = cls(**filtered)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
                logger.error("Error loading config (%s); using defaults", e)
                config = cls()
        else:
            logger.info("No config file found at %s, using defaults", config_path)

        config._apply_env_overrides()
        config.validate()
        return config

    def _apply_env_overrides(self) -> None:
        """Let environment variables override file/default values (api key only)."""
        env_key = os.environ.get(ENV_API_KEY) or os.environ.get(ENV_API_KEY_FALLBACK)
        if env_key:
            self.api_key = env_key

    def validate(self) -> None:
        """Clamp values to sane ranges so a bad config never crashes the engine."""
        if self.provider not in VALID_PROVIDERS:
            logger.warning(
                "Unknown provider %r; falling back to %s", self.provider, DEFAULT_PROVIDER
            )
            self.provider = DEFAULT_PROVIDER
        self.debounce_ms = max(0, int(self.debounce_ms))
        self.max_predictions = max(1, int(self.max_predictions))
        self.max_suggestion_words = max(1, int(self.max_suggestion_words))
        self.min_buffer_length = max(1, int(self.min_buffer_length))
        self.max_context_length = max(16, int(self.max_context_length))
        self.cache_max_entries = max(1, int(self.cache_max_entries))
        self.cache_ttl_seconds = max(0, int(self.cache_ttl_seconds))
        if not isinstance(self.blocklist_apps, list):
            self.blocklist_apps = []

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())


def _config_path() -> Path:
    """Resolve the config path, honouring the MINDFLOW_CONFIG override."""
    override = os.environ.get(ENV_CONFIG_FILE)
    return Path(override) if override else CONFIG_FILE
