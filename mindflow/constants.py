"""MindFlow constants."""

from pathlib import Path

APP_NAME = "mindflow"
COMPONENT_NAME = "org.freedesktop.IBus.MindFlow"
ENGINE_NAME = "mindflow"
ENGINE_LONG_NAME = "MindFlow AI Autocomplete"
ENGINE_DESCRIPTION = "AI-powered system-wide autocomplete using Gemini"
AUTHOR = "Seemoo"
LICENSE = "MIT"
HOMEPAGE = "https://github.com/simoabid/MindFlow"
VERSION_NOTE = "System-wide AI autocomplete for Linux, powered by Google Gemini."

# Provider identifiers
PROVIDER_GEMINI = "gemini"
PROVIDER_LOCAL = "local"
DEFAULT_PROVIDER = PROVIDER_GEMINI

# Gemini settings
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
MAX_PREDICTIONS = 6
MAX_SUGGESTION_WORDS = 12
MAX_CONTEXT_LENGTH = 200  # chars of context to send

# IBus engine settings
DEBOUNCE_MS = 300  # ms to wait before requesting prediction
MIN_BUFFER_LENGTH = 3  # minimum chars before triggering prediction

# Caching
CACHE_MAX_ENTRIES = 256  # max cached contexts before evicting least-recently-used
CACHE_TTL_SECONDS = 600  # how long a cached prediction stays fresh

# Filesystem layout (honours XDG base directory spec)
CONFIG_DIR = Path.home() / ".config" / "mindflow"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_DIR = Path.home() / ".local" / "state" / "mindflow"
STATS_FILE = STATE_DIR / "stats.json"

# Environment variables that override config values
ENV_API_KEY = "MINDFLOW_API_KEY"
ENV_API_KEY_FALLBACK = "GEMINI_API_KEY"
ENV_CONFIG_FILE = "MINDFLOW_CONFIG"
