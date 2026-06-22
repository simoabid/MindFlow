# 🪄 MindFlow — AI Autocomplete for Linux

System-wide AI-powered text autocomplete powered by Google Gemini.

**Type anywhere → See AI predictions in the IBus candidate UI → Press Tab to accept.**

## Features

- 🌍 Works in **every** app (browser, terminal, editor, chat...)
- 🧠 Powered by Gemini Flash for fast predictions
- ⌨️ Transparent typing: normal keys pass through to the app
- ⌨️ Tab to accept, Escape to dismiss
- 💾 Smart caching to minimize API calls
- 🔒 Runs as IBus input method — no root, no keylogger
- ✅ Works on Wayland and X11

## Requirements

- Linux with IBus (Zorin OS, Ubuntu, Fedora, etc.)
- Python 3.10+
- Google Gemini API key ([Get one free](https://aistudio.google.com/apikey))

## Quick Install

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

## Usage

1. Select MindFlow as your input method (Super+Space)
2. Start typing in any app
3. Predictions appear automatically after a few characters
4. Press **Up/Down** to highlight a different prediction
5. Press **Tab** to accept the highlighted prediction
6. Click a prediction in the popup to accept it
7. Press **Escape** to dismiss predictions

## Configuration

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

## Uninstall

```bash
chmod +x uninstall.sh
./uninstall.sh
```

## How It Works

```
You type → IBus observes keys while apps receive normal input
→ MindFlow buffers context → Sends to Gemini API → Shows predictions in the candidate UI
→ Tab inserts the prediction into the app
```

Built as a custom IBus input method engine — the Linux-native way.

## License

MIT
