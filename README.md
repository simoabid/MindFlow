# 🪄 MindFlow — AI Autocomplete for Linux

System-wide AI-powered text autocomplete powered by Google Gemini.

**Type anywhere → See AI predictions → Press Tab to accept.**

## Features

- 🌍 Works in **every** app (browser, terminal, editor, chat...)
- 🧠 Powered by Gemini Flash for fast predictions
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
4. Press **Tab** to accept the top prediction
5. Press **Escape** to dismiss predictions

## Configuration

Edit `~/.config/mindflow/config.json`:

```json
{
  "api_key": "YOUR_GEMINI_API_KEY",
  "model": "gemini-2.0-flash",
  "enabled": true,
  "debounce_ms": 300,
  "max_predictions": 3,
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
You type → IBus intercepts → MindFlow buffers context
→ Sends to Gemini API → Shows predictions in candidate bar
→ Tab inserts the prediction into the app
```

Built as a custom IBus input method engine — the Linux-native way.

## License

MIT
