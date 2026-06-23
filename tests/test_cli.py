# tests/test_cli.py
import json

import pytest

from mindflow import __version__
from mindflow.cli import main


@pytest.fixture
def local_config(tmp_path, monkeypatch):
    """Point the CLI at a temp config that uses the offline local provider."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"provider": "local"}))
    monkeypatch.setenv("MINDFLOW_CONFIG", str(config_path))
    monkeypatch.delenv("MINDFLOW_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    return config_path


def test_version(capsys):
    assert main(["version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_version_flag(capsys):
    assert main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_doctor_runs(local_config, capsys):
    rc = main(["doctor"])
    out = capsys.readouterr().out
    assert "diagnostics" in out
    assert rc in (0, 1)


def test_predict_local(local_config, capsys):
    assert main(["predict", "Thank you for your "]) == 0
    out = capsys.readouterr().out
    assert out.strip()  # should print at least one suggestion
    assert "[1]" in out


def test_predict_json(local_config, capsys):
    assert main(["predict", "Thank you for your ", "--json"]) == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list)


def test_config_path(local_config, capsys):
    assert main(["config", "path"]) == 0
    assert str(local_config) in capsys.readouterr().out


def test_config_set_and_get(local_config, capsys):
    assert main(["config", "set", "max_predictions", "9"]) == 0
    capsys.readouterr()
    assert main(["config", "get", "max_predictions"]) == 0
    assert capsys.readouterr().out.strip() == "9"


def test_config_set_bool(local_config, capsys):
    assert main(["config", "set", "enabled", "false"]) == 0
    capsys.readouterr()
    main(["config", "get", "enabled"])
    assert capsys.readouterr().out.strip() == "false"


def test_config_set_list(local_config, capsys):
    assert main(["config", "set", "blocklist_apps", "firefox, gnome-terminal"]) == 0
    capsys.readouterr()
    main(["config", "get", "blocklist_apps"])
    assert json.loads(capsys.readouterr().out) == ["firefox", "gnome-terminal"]


def test_config_set_unknown_key(local_config, capsys):
    assert main(["config", "set", "nope", "1"]) == 1
    assert "Unknown config key" in capsys.readouterr().out


def test_config_show_masks_api_key(local_config, capsys):
    main(["config", "set", "api_key", "supersecretkey1234"])
    capsys.readouterr()
    main(["config", "show"])
    out = capsys.readouterr().out
    assert "supersecretkey1234" not in out
    assert "***1234" in out


def test_config_show_reveals_with_flag(local_config, capsys):
    main(["config", "set", "api_key", "supersecretkey1234"])
    capsys.readouterr()
    main(["config", "show", "--show-secrets"])
    assert "supersecretkey1234" in capsys.readouterr().out


def test_stats_display_and_reset(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("mindflow.cli.STATS_FILE", tmp_path / "stats.json")
    assert main(["stats"]) == 0
    assert "usage stats" in capsys.readouterr().out
    assert main(["stats", "--reset"]) == 0
    assert "reset" in capsys.readouterr().out.lower()
