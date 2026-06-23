# 🪄 MindFlow — AI Autocomplete for Linux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![IBus](https://img.shields.io/badge/IBus-1.5+-orange.svg)](https://github.com/ibus/ibus)
[![Wayland](https://img.shields.io/badge/Wayland-Ready-green.svg)](https://wayland.freedesktop.org/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

System-wide AI-powered text autocomplete for Linux — powered by Google Gemini, with a fully offline local mode that needs no API key.

**Type anywhere → See predictions in the IBus candidate UI → Press Tab to accept.**

<p align="center">
  <em>Works in every app. No root. No keylogger. Wayland-native. Works offline.</em>
</p>

---

## ✨ Features

- 🌍 **Universal** — Works in every app (browser, terminal, editor, chat...)
- 🧠 **AI-Powered** — Fast predictions via Google Gemini Flash
- 📴 **Offline Mode** — Built-in local n-gram provider works with **no API key** and learns from what you accept
- 🔌 **Pluggable Providers** — Choose `gemini`, `local`, or Gemini with automatic local fallback
- ⌨️ **Transparent Typing** — Your keys go to the app, not the engine
- 🔼🔽 **Navigation** — Arrow keys to browse predictions
- 🖱️ **Click to Accept** — Click predictions in the popup
- 💾 **Smart Caching** — Bounded LRU + TTL cache minimizes API calls
- 🔒 **Privacy First** — Auto-disables in password/PIN fields; opt-out local-only usage stats
- 🛠️ **CLI Included** — `mindflow doctor`, `predict`, `repl`, `config`, `stats`
- ✅ **Wayland & X11** — Works on both display servers

## 📋 Requirements

- Linux with IBus (Ubuntu, Zorin OS, Fedora, etc.)
- Python 3.10+
- *(Optional)* Google Gemini API key ([get one free](https://aistudio.google.com/apikey)) — without it, MindFlow runs in offline local mode

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt install -y ibus libibus-1.0-dev gir1.2-ibus-1.0 python3-gi
```

**Fedora:**
```bash
sudo dnf install ibus ibus-devel python3-gobject
```

**Arch:**
```bash
sudo pacman -S ibus python-gobject
```

## 🚀 Quick Install

```bash
git clone https://github.com/simoabid/MindFlow.git
cd MindFlow
chmod +x install.sh
./install.sh
```

MindFlow works out of the box in **offline local mode**. To enable Gemini
predictions, provide an API key via either:

```bash
# Option A: environment variable (also picks up GEMINI_API_KEY)
export MINDFLOW_API_KEY="YOUR_GEMINI_API_KEY"

# Option B: config file
mindflow config set api_key YOUR_GEMINI_API_KEY
mindflow config set provider gemini
```

Run `mindflow doctor` at any time to check your setup.

## 📖 Usage

1. **Select MindFlow** as your input method (`Super+Space`)
2. **Start typing** in any app
3. **Predictions appear** automatically after a few characters
4. **Press ↑/↓** to highlight a different prediction
5. **Press Tab** to accept the highlighted prediction
6. **Click** a prediction in the popup to accept it
7. **Press Escape** to dismiss predictions

## ⚙️ Configuration

Edit `~/.config/mindflow/config.json`:

```json
{
  "api_key": "",
  "provider": "gemini",
  "model": "gemini-3.1-flash-lite-preview",
  "enabled": true,
  "debounce_ms": 300,
  "max_predictions": 6,
  "max_suggestion_words": 12,
  "min_buffer_length": 3,
  "cache_max_entries": 256,
  "cache_ttl_seconds": 600,
  "disable_in_password_fields": true,
  "blocklist_apps": [],
  "stats_enabled": true
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `api_key` | `""` | Your Google Gemini API key (optional) |
| `provider` | `gemini` | `gemini` (with local fallback) or `local` (fully offline) |
| `model` | `gemini-3.1-flash-lite-preview` | Gemini model to use |
| `enabled` | `true` | Enable/disable MindFlow |
| `debounce_ms` | `300` | Milliseconds to wait before requesting predictions |
| `max_predictions` | `6` | Maximum number of predictions to show |
| `max_suggestion_words` | `12` | Maximum words per prediction |
| `min_buffer_length` | `3` | Minimum characters before triggering predictions |
| `cache_max_entries` | `256` | Max entries in the LRU cache |
| `cache_ttl_seconds` | `600` | Seconds before a cached prediction expires |
| `disable_in_password_fields` | `true` | Suppress predictions in password/PIN fields |
| `blocklist_apps` | `[]` | Reserved for upcoming per-app disabling (not yet enforced) |
| `stats_enabled` | `true` | Track local usage stats (never leaves your machine) |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MINDFLOW_API_KEY` / `GEMINI_API_KEY` | Override the configured API key |
| `MINDFLOW_CONFIG` | Path to an alternate config file |

## 🖥️ CLI

MindFlow ships a `mindflow` command for setup and testing from the terminal:

```bash
mindflow doctor                       # Diagnose environment, bindings, provider
mindflow predict "I am writing to"    # Print predictions for some context
mindflow predict --json "hello"       # ...as JSON
mindflow repl                         # Interactive prediction prompt
mindflow config show                  # Print current config
mindflow config set provider local    # Switch to offline mode
mindflow stats                        # Show local usage stats
mindflow version
```

## 🔧 How It Works

```
You type → IBus observes keys while apps receive normal input
→ MindFlow buffers context → Sends to Gemini API
→ Shows predictions in the IBus candidate UI
→ Tab inserts the prediction into the app
```

Built as a custom IBus input method engine — the Linux-native way.

## 📁 Project Structure

```
MindFlow/
├── mindflow/
│   ├── __init__.py          # Package init (version)
│   ├── constants.py         # App constants & XDG paths
│   ├── config.py            # Configuration (env overrides, validation)
│   ├── cache.py             # Bounded LRU + TTL cache
│   ├── stats.py             # Local usage stats tracker
│   ├── gemini_client.py     # Gemini API wrapper
│   ├── predictor.py         # Prediction orchestration & caching
│   ├── cli.py               # `mindflow` command-line interface
│   ├── engine.py            # IBus engine (core logic)
│   └── providers/
│       ├── base.py          # PredictionProvider interface
│       ├── gemini.py        # Gemini-backed provider
│       ├── local.py         # Offline n-gram provider
│       └── __init__.py      # Provider factory + fallback wrapper
├── data/
│   ├── mindflow.xml         # IBus component descriptor
│   └── mindflow-engine.xml  # Engine metadata
├── tests/                   # 82 unit tests
├── .github/workflows/ci.yml # Lint + test matrix CI
├── install.sh / uninstall.sh
├── Makefile                 # dev/lint/format/typecheck/test/check
└── pyproject.toml           # Packaging, scripts, tool config
```

## 🧪 Testing

```bash
# Install dev dependencies
make dev          # or: pip install -e ".[dev]"

# Run the full check suite (lint + format + typecheck + tests)
make check

# Individual targets
make test         # pytest
make lint         # ruff check
make format       # ruff format
make typecheck    # mypy
make cov          # tests with coverage

# Run the integration test (requires a real API key)
python tests/integration_test.py
```

## 🗑️ Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest tests/ -v`)
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 🐛 Bug Reports

Found a bug? Please open an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

## 💡 Feature Requests

Have an idea? Please open an issue using the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [IBus](https://github.com/ibus/ibus) — The input bus framework
- [Google Gemini](https://ai.google.dev/) — AI-powered text predictions
- [Python GObject Introspection](https://pygobject.readthedocs.io/) — Python bindings for IBus

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/simoabid/MindFlow/issues)
- **Discussions:** [GitHub Discussions](https://github.com/simoabid/MindFlow/discussions)

---

<p align="center">
  Made with ❤️ for the Linux community
</p>
