# Changelog

All notable changes to MindFlow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned (Privacy & Local-First)

- **Local LLM mode** — Ollama/llama.cpp support with small models (Phi-3, Qwen2.5 0.5B). Slower but fully private, no data leaves the machine
- **Hybrid mode** — Local model for basic predictions, cloud API only for complex/long-context queries
- **Per-app whitelisting** — Only activate MindFlow in user-specified applications (e.g., browser, editor) while keeping it disabled in sensitive apps (terminals, password managers)
- **Self-hosted API option** — Point to your own endpoint (local server, private cloud, or alternative AI provider) instead of Google's Gemini

### Added
- Arrow key navigation (Up/Down/PageUp/PageDown) for prediction selection
- Click support for accepting predictions from IBus candidate popup
- `COMPONENT_NAME` constant for IBus D-Bus name ownership
- `MAX_SUGGESTION_WORDS` constant (12) for configurable word limit
- `max_suggestion_words` config field
- `_clean_prediction()` method in GeminiClient for normalizing output
- `_ensure_ibus_address()` to read IBUS_ADDRESS from config file
- `_ibus_address_from_file()` helper for parsing bus files
- `_create_component()` helper extracted from main()
- `test_engine_bootstrap.py` with 7 new engine unit tests
- Tests for configurable prompt and response limits
- Test for display settings passthrough from Predictor to GeminiClient
- CONTRIBUTING.md with development guidelines
- CHANGELOG.md (this file)
- LICENSE (MIT)

### Changed
- **BREAKING:** Transparent typing — regular keys now pass through to apps instead of being captured by preedit
- **BREAKING:** Use IBus LookupTable for prediction popup instead of auxiliary text
- Increase `MAX_PREDICTIONS` from 3 to 6
- GeminiClient constructor accepts `max_predictions` and `max_suggestion_words` params
- Prompt template uses configurable word limit (`{max_suggestion_words}`)
- Predictor passes display settings to GeminiClient
- Use `IBus.KEY_*` constants instead of `IBus.Key.*`
- Use `license=` keyword instead of `license_=` in IBus constructors
- Logging level changed from DEBUG to INFO
- Venv created with `--system-site-packages` (required for GI bindings)
- Launcher script reads IBUS_ADDRESS from `~/.config/ibus/bus/*`
- Install script tries `ibus-daemon -drx` if `ibus restart` fails
- Install script waits for IBus bus address after restart
- README updated for new features and navigation

### Fixed
- **CRITICAL:** IBus engine registration — use `bus.request_name()` when launched with `--ibus` (IBus XML activation requires D-Bus name ownership)
- **CRITICAL:** Factory uses `MindFlowEngine.__gtype__` for `add_engine` (C-level requirement)
- Factory uses `IBus.Factory(bus=bus)` to set `object_path` correctly
- Remove unsupported `license_` parameter from IBus constructors
- `_is_active` flag checked in `do_process_key_event`
- Thread safety on `_context_buffer` (snapshot under lock)
- Thread deduplication via `_last_requested_context`
- `response.text` None handling in GeminiClient
- Venv recreation if missing `--system-site-packages`

### Removed
- `MindFlowEngineFactory` class (unused)
- `_update_preedit()` and `_commit_preedit()` methods (transparent typing)
- `_trigger_prediction()` direct thread spawning (replaced with GLib.timeout_add)

## [0.2.0] - 2026-06-23

### Added
- **Pluggable provider architecture** (`mindflow/providers/`) — `gemini` and an
  offline `local` n-gram provider, with a `FallbackProvider` that uses Gemini
  when a key is configured and transparently falls back to the local model
  otherwise. MindFlow now works with **no API key**.
- **Offline local provider** that learns from accepted text and persists a
  small human-readable history to `~/.local/state/mindflow/local_history.json`.
- **`mindflow` CLI** with subcommands: `doctor` (environment diagnostics),
  `config` (show/path/edit/get/set), `predict`, `repl`, `stats`, `version`.
- **Bounded LRU + TTL cache** (`mindflow/cache.py`) with hit/miss accounting.
- **Local usage stats** (`mindflow/stats.py`) persisted to
  `~/.local/state/mindflow/stats.json`; opt-out via `stats_enabled`.
- **Privacy**: predictions are suppressed in password/PIN input fields. A
  `blocklist_apps` config field is reserved for upcoming per-app disabling
  (declared but not yet enforced by the engine).
- Config: environment-variable overrides (`MINDFLOW_API_KEY`/`GEMINI_API_KEY`,
  `MINDFLOW_CONFIG`), `validate()`, and new `provider`/privacy/cache fields.
- Modern packaging via `pyproject.toml` (console scripts `mindflow` and
  `mindflow-engine`), `Makefile`, GitHub Actions CI (lint + 3.10/3.11/3.12
  test matrix), and pre-commit hooks (ruff, ruff-format, mypy).
- Expanded test suite to 82 tests covering providers, cache, stats, CLI, config
  overrides, and engine privacy behaviour.

### Changed
- `Predictor` now owns a `PredictionProvider` instead of a `GeminiClient`
  directly, and is built via `Predictor.from_config(...)`.
- `GeminiClient` honours configured limits and budgets enough output tokens for
  the requested number/length of predictions; dedupes repeated predictions.

### Fixed
- Dismissing predictions no longer wipes the whole cache — `clear_pending()`
  clears only the in-flight UI suggestions, keeping the cache warm.
- Malformed `<symbol>` tag in `data/mindflow-engine.xml`.
- Stale `seemoo` homepage URLs updated to `simoabid/MindFlow`.

### Removed
- `setup.py` (superseded by `pyproject.toml`).

## [0.1.0] - 2026-06-22

### Added
- Initial release
- Project scaffolding with Python package structure
- Gemini API client (`gemini_client.py`) with text prediction
- Prediction manager (`predictor.py`) with caching and debouncing
- Configuration manager (`config.py`) with JSON persistence
- IBus engine (`engine.py`) with keystroke handling
- One-command installation script (`install.sh`)
- Uninstallation script (`uninstall.sh`)
- Integration test for full Gemini pipeline
- README with full documentation
- `.gitignore` for Python artifacts

---

## Commit History

### v0.1.0 (Initial Release)

| Commit | Type | Description |
|--------|------|-------------|
| `35ee777` | feat | Project scaffolding with dependencies |
| `30ab3fa` | chore | Add .gitignore |
| `4513f87` | feat | Gemini API client for text predictions |
| `f94e1c3` | fix | Handle None response.text and mock API in tests |
| `a2c175e` | feat | Prediction manager with caching and debouncing |
| `bc482f7` | feat | Configuration manager with JSON persistence |
| `6125e8b` | feat | IBus engine with keystroke handling and prediction display |
| `ad09456` | fix | Thread safety, active flag check, and thread deduplication |
| `338488e` | feat | One-command installation script |
| `dc8e29e` | feat | Integration test for full pipeline verification |
| `ab74b39` | docs | README and uninstall script |

### Post-Release Fixes

| Commit | Type | Description |
|--------|------|-------------|
| `518e267` | chore | Update default model to gemini-3.1-flash-lite-preview |
| `1730c05` | docs | Project context and debug history for next AI |
| `542d9b5` | fix | Update logging level and refactor engine factory creation |

### Unreleased (Current)

| Commit | Type | Description |
|--------|------|-------------|
| `5329675` | feat | Add COMPONENT_NAME, MAX_SUGGESTION_WORDS, increase MAX_PREDICTIONS to 6 |
| `60107c4` | feat | Configurable prediction count and word limits in GeminiClient |
| `c1e58f0` | feat | Pass display settings from Predictor to GeminiClient |
| `2c3d317` | fix | IBus engine registration + transparent typing + lookup table UI |
| `d3aa360` | fix | Venv with system-site-packages, launcher IBUS_ADDRESS, IBus restart |
| `5dbfd73` | test | Update existing tests + add engine bootstrap tests |
| `0b96384` | docs | Update README for transparent typing, navigation, and new defaults |

---

## Release Notes

### What is MindFlow?

MindFlow is a system-wide AI-powered text autocomplete for Linux. It runs as an IBus input method engine, using Google Gemini to predict what you're about to type.

**Key Features:**
- 🌍 Works in every app (browser, terminal, editor, chat)
- 🧠 Powered by Gemini Flash for fast predictions
- ⌨️ Transparent typing — your keys go to the app, not the engine
- 🔼🔽 Arrow key navigation through predictions
- 🖱️ Click to accept predictions
- 💾 Smart caching to minimize API calls
- 🔒 Runs as IBus input method — no root, no keylogger
- ✅ Works on Wayland and X11

### Installation

```bash
git clone https://github.com/seemoo/mindflow.git
cd mindflow
./install.sh
```

### Requirements

- Linux with IBus (Ubuntu, Zorin OS, Fedora, etc.)
- Python 3.10+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
