import os
import threading
from types import SimpleNamespace

import pytest
import gi

gi.require_version("IBus", "1.0")
from gi.repository import IBus

from mindflow.engine import MindFlowEngine, _ensure_ibus_address


def _make_uninitialized_engine(monkeypatch, min_buffer_length=1, debounce_ms=0):
    engine = MindFlowEngine.__new__(MindFlowEngine)
    engine.config = SimpleNamespace(
        min_buffer_length=min_buffer_length,
        debounce_ms=debounce_ms,
    )
    engine.predictor = SimpleNamespace(clear_cache=lambda: None)
    engine._preedit_text = ""
    engine._context_buffer = ""
    engine._predictions = []
    engine._selected_prediction_index = 0
    engine._is_active = True
    engine._prediction_lock = threading.Lock()
    engine._last_requested_context = ""
    engine._prediction_timer_id = 0
    engine.update_preedit_text = lambda *args: None
    engine.update_lookup_table = lambda *args: None
    engine.show_lookup_table = lambda: None
    engine.update_auxiliary_text = lambda *args: None
    engine.show_auxiliary_text = lambda: None
    engine.hide_auxiliary_text = lambda: None
    engine.hide_lookup_table = lambda: None
    return engine


def test_ensure_ibus_address_preserves_existing_value(monkeypatch):
    monkeypatch.setenv("IBUS_ADDRESS", "existing-address")

    assert _ensure_ibus_address() is True
    assert os.environ["IBUS_ADDRESS"] == "existing-address"


def test_ensure_ibus_address_reads_bus_file(monkeypatch, tmp_path):
    bus_dir = tmp_path / ".config" / "ibus" / "bus"
    bus_dir.mkdir(parents=True)
    address = "unix:path=/tmp/ibus-test,guid=abc=def"
    (bus_dir / "test-bus").write_text(
        "# created by ibus-daemon\n"
        f"IBUS_ADDRESS={address}\n"
        "IBUS_DAEMON_PID=123\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("IBUS_ADDRESS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert _ensure_ibus_address() is True
    assert os.environ["IBUS_ADDRESS"] == address


def test_regular_character_passes_through_and_schedules_prediction(monkeypatch):
    engine = _make_uninitialized_engine(monkeypatch, debounce_ms=250)
    scheduled = []

    def fake_timeout_add(delay_ms, callback, context):
        scheduled.append((delay_ms, callback, context))
        return 42

    monkeypatch.setattr("mindflow.engine.GLib.timeout_add", fake_timeout_add)

    handled = engine.do_process_key_event(ord("a"), 0, 0)

    assert handled is False
    assert engine._context_buffer == "a"
    assert scheduled[0][0] == 250
    assert scheduled[0][2] == "a"


def test_tab_accepts_prediction_without_retyping_context(monkeypatch):
    engine = _make_uninitialized_engine(monkeypatch)
    committed = []
    engine._context_buffer = "hello"
    engine._predictions = ["world"]
    engine.commit_text = lambda text: committed.append(text.get_text())

    handled = engine.do_process_key_event(IBus.KEY_Tab, 0, 0)

    assert handled is True
    assert committed == [" world"]
    assert engine._context_buffer == "hello world"


def test_down_arrow_selects_next_prediction_for_tab_accept(monkeypatch):
    engine = _make_uninitialized_engine(monkeypatch)
    committed = []
    engine._context_buffer = "hello"
    engine._predictions = ["world", "there", "friend"]
    engine.commit_text = lambda text: committed.append(text.get_text())

    handled_down = engine.do_process_key_event(IBus.KEY_Down, 0, 0)
    handled_tab = engine.do_process_key_event(IBus.KEY_Tab, 0, 0)

    assert handled_down is True
    assert handled_tab is True
    assert committed == [" there"]


def test_candidate_click_accepts_clicked_prediction(monkeypatch):
    engine = _make_uninitialized_engine(monkeypatch)
    committed = []
    engine._context_buffer = "hello"
    engine._predictions = ["world", "there", "friend"]
    engine.commit_text = lambda text: committed.append(text.get_text())

    engine.do_candidate_clicked(2, 1, 0)

    assert committed == [" friend"]


def test_reset_allows_same_context_to_request_again(monkeypatch):
    engine = _make_uninitialized_engine(monkeypatch)
    engine._context_buffer = "The weather today is"
    engine._last_requested_context = "The weather today is"

    engine.do_reset()

    assert engine._context_buffer == ""
    assert engine._last_requested_context == ""
