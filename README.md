# 🪄 MindFlow — AI Autocomplete for Linux

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![IBus](https://img.shields.io/badge/IBus-1.5+-orange.svg)](https://github.com/ibus/ibus)
[![Wayland](https://img.shields.io/badge/Wayland-Ready-green.svg)](https://wayland.freedesktop.org/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)

System-wide AI-powered text autocomplete powered by Google Gemini.

**Type anywhere → See AI predictions in the IBus candidate UI → Press Tab to accept.**

<p align="center">
  <em>Works in every app. No root. No keylogger. Wayland-native.</em>
</p>

---

## ✨ Features

- 🌍 **Universal** — Works in every app (browser, terminal, editor, chat...)
- 🧠 **AI-Powered** — Fast predictions via Google Gemini Flash
- ⌨️ **Transparent Typing** — Your keys go to the app, not the engine
- 🔼🔽 **Navigation** — Arrow keys to browse predictions
- 🖱️ **Click to Accept** — Click predictions in the popup
- 💾 **Smart Caching** — Minimizes API calls
- 🔒 **Secure** — Runs as IBus input method, no root needed
- ✅ **Wayland & X11** — Works on both display servers

## 📋 Requirements

- Linux with IBus (Ubuntu, Zorin OS, Fedora, etc.)
- Python 3.10+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))

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
git clone https://github.com/seemoo/mindflow.git
cd mindflow
chmod +x install.sh
./install.sh
```

Then set your API key:
```bash
# Edit ~/.config/mindflow/config.json
# Set "api_key": "YOUR_GEMINI_API_KEY"
```

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
  "api_key": "YOUR_GEMINI_API_KEY",
  "model": "gemini-3.1-flash-lite-preview",
  "enabled": true,
  "debounce_ms": 300,
  "max_predictions": 6,
  "max_suggestion_words": 12,
  "min_buffer_length": 3
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `api_key` | `""` | Your Google Gemini API key |
| `model` | `gemini-3.1-flash-lite-preview` | Gemini model to use |
| `enabled` | `true` | Enable/disable MindFlow |
| `debounce_ms` | `300` | Milliseconds to wait before requesting predictions |
| `max_predictions` | `6` | Maximum number of predictions to show |
| `max_suggestion_words` | `12` | Maximum words per prediction |
| `min_buffer_length` | `3` | Minimum characters before triggering predictions |

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
mindflow/
├── mindflow/
│   ├── __init__.py          # Package init
│   ├── constants.py         # App constants
│   ├── config.py            # Configuration management
│   ├── gemini_client.py     # Gemini API wrapper
│   ├── predictor.py         # Prediction caching & debouncing
│   └── engine.py            # IBus engine (core logic)
├── data/
│   ├── mindflow.xml         # IBus component descriptor
│   └── mindflow-engine.xml  # Engine metadata
├── tests/
│   ├── test_config.py       # Config tests
│   ├── test_gemini_client.py # Gemini client tests
│   ├── test_predictor.py    # Predictor tests
│   ├── test_engine_bootstrap.py # Engine unit tests
│   └── integration_test.py  # Manual integration test
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
└── setup.py                 # Package configuration
```

## 🧪 Testing

```bash
# Run all unit tests
pytest tests/ -v

# Run integration test (requires API key)
python tests/integration_test.py

# Run with coverage
pytest tests/ --cov=mindflow --cov-report=html
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

- **Issues:** [GitHub Issues](https://github.com/seemoo/mindflow/issues)
- **Discussions:** [GitHub Discussions](https://github.com/seemoo/mindflow/discussions)

---

<p align="center">
  Made with ❤️ for the Linux community
</p>
