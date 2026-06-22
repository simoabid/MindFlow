"""MindFlow constants."""

APP_NAME = "mindflow"
COMPONENT_NAME = "org.freedesktop.IBus.MindFlow"
ENGINE_NAME = "mindflow"
ENGINE_LONG_NAME = "MindFlow AI Autocomplete"
ENGINE_DESCRIPTION = "AI-powered system-wide autocomplete using Gemini"
AUTHOR = "Seemoo"
LICENSE = "MIT"

# Gemini settings
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
MAX_PREDICTIONS = 6
MAX_SUGGESTION_WORDS = 12
MAX_CONTEXT_LENGTH = 200  # chars of context to send

# IBus engine settings
DEBOUNCE_MS = 300  # ms to wait before requesting prediction
MIN_BUFFER_LENGTH = 3  # minimum chars before triggering prediction
