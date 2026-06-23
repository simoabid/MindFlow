# mindflow/cli.py
"""Command-line interface for MindFlow.

Provides diagnostics, configuration management and a way to try predictions
from a terminal (handy for testing without a full IBus/GUI session).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, fields

from . import __version__
from .config import MindFlowConfig, _config_path
from .constants import (
    APP_NAME,
    ENGINE_LONG_NAME,
    STATS_FILE,
    VERSION_NOTE,
)
from .predictor import Predictor
from .stats import StatsTracker


def _print(msg: str = "") -> None:
    print(msg)


def _ok(msg: str) -> str:
    return f"  [OK]   {msg}"


def _warn(msg: str) -> str:
    return f"  [WARN] {msg}"


def _fail(msg: str) -> str:
    return f"  [FAIL] {msg}"


# --------------------------------------------------------------------- commands
def cmd_version(args: argparse.Namespace) -> int:
    _print(f"{ENGINE_LONG_NAME} v{__version__}")
    if VERSION_NOTE:
        _print(VERSION_NOTE)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    _print(f"🩺 {ENGINE_LONG_NAME} diagnostics\n")
    problems = 0

    # 1. Python
    _print(_ok(f"Python {sys.version.split()[0]}"))

    # 2. PyGObject / IBus bindings
    try:
        import gi

        gi.require_version("IBus", "1.0")
        from gi.repository import IBus

        version = f"{IBus.MAJOR_VERSION}.{IBus.MINOR_VERSION}.{IBus.MICRO_VERSION}"
        _print(_ok(f"PyGObject + IBus bindings ({version})"))
    except (ImportError, ValueError) as e:
        problems += 1
        _print(_fail(f"IBus Python bindings missing: {e}"))
        _print("         Install: sudo apt install python3-gi gir1.2-ibus-1.0")

    # 3. ibus binary
    if shutil.which("ibus"):
        _print(_ok("ibus binary found on PATH"))
    else:
        problems += 1
        _print(_fail("ibus binary not found — is IBus installed?"))

    # 4. google-genai
    try:
        import google.genai  # noqa: F401

        _print(_ok("google-genai SDK importable"))
    except ImportError:
        _print(_warn("google-genai not installed (only needed for the Gemini provider)"))

    # 5. Config
    config_path = _config_path()
    if config_path.exists():
        _print(_ok(f"Config file: {config_path}"))
    else:
        _print(_warn(f"No config file yet at {config_path} (defaults in use)"))

    config = MindFlowConfig.load()
    _print(_ok(f"Provider: {config.provider}"))
    if config.provider == "gemini":
        if config.has_api_key:
            _print(_ok("Gemini API key is set"))
        else:
            _print(
                _warn(
                    "No Gemini API key — predictions will fall back to the offline "
                    "local provider. Set 'api_key' in config or $MINDFLOW_API_KEY."
                )
            )

    # 6. Provider self-test
    try:
        predictor = Predictor.from_config(config)
        available = predictor.provider.describe()
        _print(_ok(f"Prediction backend ready: {available}"))
    except Exception as e:  # pragma: no cover - defensive
        problems += 1
        _print(_fail(f"Could not initialise provider: {e}"))

    _print()
    if problems == 0:
        _print("All core checks passed. 🪄")
    else:
        _print(f"{problems} problem(s) found — see [FAIL] lines above.")
    return 1 if problems else 0


def cmd_predict(args: argparse.Namespace) -> int:
    config = MindFlowConfig.load()
    predictor = Predictor.from_config(config)
    text = args.text if args.text else sys.stdin.read()
    predictions = predictor.get_predictions(text)
    if args.json:
        _print(json.dumps(predictions, indent=2))
    elif not predictions:
        _print("(no predictions)")
    else:
        for i, prediction in enumerate(predictions, 1):
            _print(f"  [{i}] {prediction}")
    return 0


def cmd_repl(args: argparse.Namespace) -> int:
    config = MindFlowConfig.load()
    predictor = Predictor.from_config(config)
    _print(f"{ENGINE_LONG_NAME} REPL — {predictor.provider.describe()}")
    _print("Type text to see predictions. Ctrl-D or 'exit' to quit.\n")
    while True:
        try:
            text = input("» ")
        except (EOFError, KeyboardInterrupt):
            _print()
            break
        if text.strip() in {"exit", "quit"}:
            break
        if not text.strip():
            continue
        predictions = predictor.get_predictions(text)
        if not predictions:
            _print("  (no predictions)")
        else:
            for i, prediction in enumerate(predictions, 1):
                _print(f"  [{i}] {prediction}")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    config_path = _config_path()

    if args.config_command == "path":
        _print(str(config_path))
        return 0

    if args.config_command == "show":
        config = MindFlowConfig.load()
        data = asdict(config)
        if not args.show_secrets and data.get("api_key"):
            data["api_key"] = "***" + data["api_key"][-4:]
        _print(json.dumps(data, indent=2))
        return 0

    if args.config_command == "get":
        config = MindFlowConfig.load()
        if not hasattr(config, args.key):
            _print(
                f"Unknown config key: {args.key}",
            )
            return 1
        _print(json.dumps(getattr(config, args.key)))
        return 0

    if args.config_command == "set":
        config = MindFlowConfig.load()
        valid_keys = {f.name: f.type for f in fields(MindFlowConfig)}
        if args.key not in valid_keys:
            _print(f"Unknown config key: {args.key}")
            _print(f"Valid keys: {', '.join(sorted(valid_keys))}")
            return 1
        try:
            value = _coerce_value(config, args.key, args.value)
        except ValueError as e:
            _print(f"Invalid value for {args.key}: {e}")
            return 1
        setattr(config, args.key, value)
        config.validate()
        config.save(config_path)
        _print(f"Set {args.key} = {getattr(config, args.key)!r}")
        return 0

    if args.config_command == "edit":
        editor = os.environ.get("EDITOR", "nano")
        if not config_path.exists():
            MindFlowConfig().save(config_path)
        subprocess.call([editor, str(config_path)])
        return 0

    return 1


def cmd_stats(args: argparse.Namespace) -> int:
    tracker = StatsTracker(STATS_FILE)
    if args.reset:
        tracker.reset()
        _print("Stats reset.")
        return 0
    s = tracker.stats
    _print(f"📊 {ENGINE_LONG_NAME} usage stats\n")
    _print(f"  Predictions requested : {s.predictions_requested}")
    _print(f"  Predictions shown     : {s.predictions_shown}")
    _print(f"  Suggestions accepted  : {s.suggestions_accepted}")
    _print(f"  Suggestions dismissed : {s.suggestions_dismissed}")
    _print(f"  Cache hits / misses   : {s.cache_hits} / {s.cache_misses}")
    _print(f"  Acceptance rate       : {s.acceptance_rate:.1%}")
    return 0


def _coerce_value(config: MindFlowConfig, key: str, raw: str) -> object:
    """Coerce a CLI string into the type of the existing config field."""
    current = getattr(config, key)
    if isinstance(current, bool):
        if raw.lower() in {"true", "1", "yes", "on"}:
            return True
        if raw.lower() in {"false", "0", "no", "off"}:
            return False
        raise ValueError("expected a boolean (true/false)")
    if isinstance(current, int):
        return int(raw)
    if isinstance(current, list):
        return [item.strip() for item in raw.split(",") if item.strip()]
    return raw


# ------------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{ENGINE_LONG_NAME} — manage and test the autocomplete engine.",
    )
    parser.add_argument("-V", "--version", action="store_true", help="show version and exit")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="show version")
    sub.add_parser("doctor", help="run environment diagnostics")

    p_predict = sub.add_parser("predict", help="print predictions for some text")
    p_predict.add_argument("text", nargs="?", help="text to complete (or read from stdin)")
    p_predict.add_argument("--json", action="store_true", help="output JSON")

    sub.add_parser("repl", help="interactive prediction prompt")

    p_config = sub.add_parser("config", help="view or change configuration")
    config_sub = p_config.add_subparsers(dest="config_command", required=True)
    p_show = config_sub.add_parser("show", help="print the effective config")
    p_show.add_argument("--show-secrets", action="store_true", help="reveal the API key")
    config_sub.add_parser("path", help="print the config file path")
    config_sub.add_parser("edit", help="open the config in $EDITOR")
    p_get = config_sub.add_parser("get", help="print one config value")
    p_get.add_argument("key")
    p_set = config_sub.add_parser("set", help="change one config value")
    p_set.add_argument("key")
    p_set.add_argument("value")

    p_stats = sub.add_parser("stats", help="show local usage statistics")
    p_stats.add_argument("--reset", action="store_true", help="reset all counters")

    return parser


_COMMANDS = {
    "version": cmd_version,
    "doctor": cmd_doctor,
    "predict": cmd_predict,
    "repl": cmd_repl,
    "config": cmd_config,
    "stats": cmd_stats,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command == "version":
        return cmd_version(args)

    if not args.command:
        parser.print_help()
        return 0

    return _COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
