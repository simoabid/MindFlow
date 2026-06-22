# mindflow/engine.py
"""MindFlow IBus Engine — AI-powered autocomplete."""

import sys
import signal
import logging
import threading
import os
from pathlib import Path
import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib

from .predictor import Predictor
from .config import MindFlowConfig
from .constants import (
    AUTHOR,
    COMPONENT_NAME,
    ENGINE_DESCRIPTION,
    ENGINE_LONG_NAME,
    ENGINE_NAME,
    LICENSE,
)

logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


class MindFlowEngine(IBus.Engine):
    """IBus engine that provides AI-powered text predictions."""

    __gtype_name__ = "MindFlowEngine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = MindFlowConfig.load()
        self.predictor = Predictor(
            api_key=self.config.api_key,
            model=self.config.model,
            max_predictions=self.config.max_predictions,
            max_suggestion_words=self.config.max_suggestion_words,
        )

        # Context buffer mirrors normal typing while key events pass through.
        self._preedit_text = ""
        self._context_buffer = ""  # Full context for predictions
        self._predictions: list[str] = []
        self._selected_prediction_index = 0
        self._is_active = True
        self._prediction_lock = threading.Lock()
        self._last_requested_context = ""
        self._prediction_timer_id = 0

        logger.info("MindFlow engine initialized")

    def do_process_key_event(self, keyval, keycode, state):
        """Process each keystroke. Return True if handled, False to pass through."""
        # Ignore key releases
        if state & IBus.ModifierType.RELEASE_MASK:
            return False

        # Don't process when engine is not active
        if not self._is_active:
            return False

        # Don't intercept when Control/Alt/Meta is held (let shortcuts through)
        if state & (IBus.ModifierType.CONTROL_MASK | IBus.ModifierType.MOD1_MASK):
            return False

        # === ACCEPT PREDICTION: Tab ===
        if keyval == IBus.KEY_Tab and self._predictions:
            self._accept_prediction()
            return True

        # === DISMISS PREDICTION: Escape ===
        if keyval == IBus.KEY_Escape and self._predictions:
            self._dismiss_predictions()
            return True

        # === NAVIGATE PREDICTIONS ===
        if self._predictions and keyval in (IBus.KEY_Down, IBus.KEY_KP_Down):
            return self._move_prediction_selection(1)

        if self._predictions and keyval in (IBus.KEY_Up, IBus.KEY_KP_Up):
            return self._move_prediction_selection(-1)

        if self._predictions and keyval == IBus.KEY_Page_Down:
            return self._move_prediction_selection(len(self._predictions) - 1)

        if self._predictions and keyval == IBus.KEY_Page_Up:
            return self._move_prediction_selection(-(len(self._predictions) - 1))

        # === BACKSPACE ===
        if keyval == IBus.KEY_BackSpace:
            if self._context_buffer:
                self._context_buffer = self._context_buffer[:-1]
                self._trigger_prediction()
            self._preedit_text = ""
            self.update_preedit_text(IBus.Text.new_from_string(""), 0, False)
            return False

        # === ENTER / RETURN ===
        if keyval in (IBus.KEY_Return, IBus.KEY_KP_Enter):
            self._context_buffer += "\n"
            self._clear_predictions()
            return False  # Let Enter pass through to the app

        # === SPACE ===
        if keyval == IBus.KEY_space:
            self._context_buffer += " "
            self._trigger_prediction()
            return False  # Let space pass through

        # === REGULAR CHARACTER ===
        char = self._keyval_to_char(keyval)
        if char:
            self._context_buffer += char
            self._trigger_prediction()
            return False

        return False

    def _keyval_to_char(self, keyval):
        """Convert IBus keyval to character."""
        if 0x20 <= keyval <= 0x7E:  # Printable ASCII
            return chr(keyval)
        return None

    def _trigger_prediction(self):
        """Schedule a prediction after the user pauses typing."""
        if len(self._context_buffer.strip()) < self.config.min_buffer_length:
            self._cancel_prediction_timer()
            self._clear_predictions()
            return

        context_snapshot = self._context_buffer
        if context_snapshot == self._last_requested_context:
            return

        self._cancel_prediction_timer()
        delay_ms = max(0, int(self.config.debounce_ms))
        self._prediction_timer_id = GLib.timeout_add(
            delay_ms,
            self._run_scheduled_prediction,
            context_snapshot,
        )

    def _cancel_prediction_timer(self):
        """Cancel a pending prediction timer, if one exists."""
        if self._prediction_timer_id:
            GLib.source_remove(self._prediction_timer_id)
            self._prediction_timer_id = 0

    def _run_scheduled_prediction(self, context_snapshot):
        """Start prediction work for the latest scheduled context."""
        self._prediction_timer_id = 0
        if context_snapshot != self._context_buffer:
            return False

        if context_snapshot == self._last_requested_context:
            return False

        self._last_requested_context = context_snapshot

        # Run prediction in background to avoid blocking UI
        thread = threading.Thread(target=self._fetch_predictions, args=(context_snapshot,), daemon=True)
        thread.start()
        return False

    def _fetch_predictions(self, context):
        """Fetch predictions from Gemini (runs in background thread)."""
        try:
            predictions = self.predictor.get_predictions(context)
            with self._prediction_lock:
                if context != self._context_buffer:
                    return
                self._predictions = predictions
                self._selected_prediction_index = 0
            # Schedule UI update on main thread
            GLib.idle_add(self._show_predictions)
        except Exception as e:
            logger.error(f"Prediction error: {e}")

    def _show_predictions(self):
        """Display predictions in the IBus auxiliary text panel."""
        if not self._predictions:
            self.hide_lookup_table()
            self.hide_auxiliary_text()
            return False

        lookup_table = IBus.LookupTable(page_size=len(self._predictions))
        for prediction in self._predictions:
            lookup_table.append_candidate(IBus.Text.new_from_string(prediction))
        lookup_table.set_cursor_visible(True)
        lookup_table.set_cursor_pos(self._clamped_prediction_index())
        self.update_lookup_table(lookup_table, True)
        self.show_lookup_table()

        text = IBus.Text.new_from_string("MindFlow predictions - Tab accepts, Esc dismisses")

        attrs = IBus.AttrList()
        attrs.append(IBus.Attribute.new(
            IBus.AttrType.FOREGROUND,
            0x00AAAAAA,  # Gray color
            0, len(text.get_text()),
        ))
        text.set_attributes(attrs)

        self.update_auxiliary_text(text, True)
        self.show_auxiliary_text()
        return False  # Remove from GLib idle queue

    def _clamped_prediction_index(self):
        """Return a selected index that is valid for the current predictions."""
        if not self._predictions:
            self._selected_prediction_index = 0
            return 0
        self._selected_prediction_index %= len(self._predictions)
        return self._selected_prediction_index

    def _move_prediction_selection(self, delta):
        """Move the highlighted prediction in the lookup table."""
        if not self._predictions:
            return False

        self._selected_prediction_index = (
            self._clamped_prediction_index() + delta
        ) % len(self._predictions)
        self._show_predictions()
        return True

    def _accept_prediction(self, index=None):
        """Accept the selected prediction and insert it."""
        with self._prediction_lock:
            if not self._predictions:
                return
            if index is None:
                index = self._clamped_prediction_index()
            if index < 0 or index >= len(self._predictions):
                return
            prediction = self._predictions[index]

        # Clear preedit
        self._preedit_text = ""
        self.update_preedit_text(IBus.Text.new_from_string(""), 0, False)

        # Commit the prediction text
        # Add a space before if context doesn't end with space
        if self._context_buffer and not self._context_buffer.endswith(" "):
            prediction = " " + prediction

        text = IBus.Text.new_from_string(prediction)
        self.commit_text(text)

        # Update context buffer
        self._context_buffer += prediction

        # Clear predictions
        self._clear_predictions()

        logger.info(f"Accepted prediction: '{prediction}'")

    def _dismiss_predictions(self):
        """Dismiss current predictions without accepting."""
        self._clear_predictions()
        logger.debug("Predictions dismissed")

    def _clear_predictions(self):
        """Clear all predictions and hide auxiliary text."""
        self._cancel_prediction_timer()
        with self._prediction_lock:
            self._predictions = []
            self._selected_prediction_index = 0
        self.predictor.clear_cache()
        self.hide_lookup_table()
        self.hide_auxiliary_text()

    def do_cursor_down(self):
        """Called by the IBus panel when the candidate cursor moves down."""
        self._move_prediction_selection(1)

    def do_cursor_up(self):
        """Called by the IBus panel when the candidate cursor moves up."""
        self._move_prediction_selection(-1)

    def do_page_down(self):
        """Called by the IBus panel when the candidate cursor pages down."""
        if self._predictions:
            self._move_prediction_selection(len(self._predictions) - 1)

    def do_page_up(self):
        """Called by the IBus panel when the candidate cursor pages up."""
        if self._predictions:
            self._move_prediction_selection(-(len(self._predictions) - 1))

    def do_candidate_clicked(self, index, button, state):
        """Accept a clicked candidate from the IBus lookup table."""
        if button == 1:
            self._accept_prediction(index)

    def do_focus_in(self):
        """Called when an input field gains focus."""
        self._is_active = True
        logger.debug("Focus in")

    def do_focus_out(self):
        """Called when an input field loses focus."""
        self._is_active = False
        self._preedit_text = ""
        self._context_buffer = ""
        self._last_requested_context = ""
        self._clear_predictions()
        logger.debug("Focus out")

    def do_reset(self):
        """Reset the engine state."""
        self._preedit_text = ""
        self._context_buffer = ""
        self._last_requested_context = ""
        self._clear_predictions()
        logger.debug("Engine reset")

    def do_enable(self):
        """Called when engine is enabled."""
        self._is_active = True
        logger.info("MindFlow enabled")

    def do_disable(self):
        """Called when engine is disabled."""
        self._is_active = False
        logger.info("MindFlow disabled")


def _ibus_address_from_file(path: Path):
    """Return IBUS_ADDRESS from an ibus bus file, if present."""
    try:
        with path.open("r", encoding="utf-8") as bus_file:
            for line in bus_file:
                if line.startswith("IBUS_ADDRESS="):
                    return line.strip().split("=", 1)[1]
    except OSError as exc:
        logger.debug("Could not read IBus bus file %s: %s", path, exc)
    return None


def _ensure_ibus_address():
    """Load the private IBus bus address when ibus-daemon did not export it."""
    if os.environ.get("IBUS_ADDRESS"):
        return True

    bus_dir = Path.home() / ".config" / "ibus" / "bus"
    try:
        bus_files = sorted(
            (path for path in bus_dir.iterdir() if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError as exc:
        logger.warning("IBUS_ADDRESS is not set and %s is not readable: %s", bus_dir, exc)
        return False

    for path in bus_files:
        address = _ibus_address_from_file(path)
        if address:
            os.environ["IBUS_ADDRESS"] = address
            logger.info("Loaded IBUS_ADDRESS from %s", path)
            return True

    logger.warning("IBUS_ADDRESS is not set and no address was found in %s", bus_dir)
    return False


def _create_component():
    """Build the IBus component descriptor used for manual registration."""
    component = IBus.Component(
        name=COMPONENT_NAME,
        description="MindFlow AI Autocomplete Engine",
        version="0.1.0",
        license=LICENSE,
        author=AUTHOR,
        homepage="https://github.com/seemoo/mindflow",
        command_line="mindflow-engine",
        textdomain="mindflow",
    )
    engine_desc = IBus.EngineDesc(
        name=ENGINE_NAME,
        longname=ENGINE_LONG_NAME,
        description=ENGINE_DESCRIPTION,
        language="en",
        license=LICENSE,
        author=AUTHOR,
        icon="input-keyboard",
        layout="us",
    )
    component.add_engine(engine_desc)
    return component


def main():
    """Main entry point for the IBus engine."""
    logger.info("Starting MindFlow IBus engine...")

    _ensure_ibus_address()
    bus = IBus.Bus()

    if not bus.is_connected():
        logger.error("Cannot connect to IBus daemon!")
        sys.exit(1)

    # Create factory and register engine type
    # NOTE: Must pass bus= (not connection=) so the Python override sets object_path
    factory = IBus.Factory(bus=bus)
    factory.add_engine(ENGINE_NAME, MindFlowEngine.__gtype__)

    if "--ibus" in sys.argv:
        # XML activation waits for this well-known name before attaching the
        # component factory and calling CreateEngine.
        name_reply = bus.request_name(COMPONENT_NAME, IBus.BusNameFlag.DO_NOT_QUEUE)
        if name_reply not in (
            IBus.BusRequestNameReply.PRIMARY_OWNER,
            IBus.BusRequestNameReply.ALREADY_OWNER,
        ):
            logger.error("Could not own IBus component name %s: %s", COMPONENT_NAME, name_reply)
            sys.exit(1)
    else:
        bus.register_component(_create_component())

    # Handle signals
    def sigterm_handler(signum, frame):
        logger.info("Received signal, shutting down...")
        IBus.quit()

    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    logger.info("MindFlow engine registered and running!")
    IBus.main()


if __name__ == "__main__":
    main()
