# mindflow/engine.py
"""MindFlow IBus Engine — AI-powered autocomplete."""

import sys
import signal
import logging
import threading
import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib

from .predictor import Predictor
from .config import MindFlowConfig
from .constants import ENGINE_NAME, ENGINE_LONG_NAME, ENGINE_DESCRIPTION

logger = logging.getLogger(__name__)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


class MindFlowEngine(IBus.Engine):
    """IBus engine that provides AI-powered text predictions."""

    __gtype_name__ = "MindFlowEngine"

    def __init__(self):
        super().__init__()
        self.config = MindFlowConfig.load()
        self.predictor = Predictor(
            api_key=self.config.api_key,
            model=self.config.model,
        )

        # Text buffer — accumulates what the user types
        self._preedit_text = ""  # Current word being typed (before space)
        self._context_buffer = ""  # Full context for predictions
        self._predictions: list[str] = []
        self._is_active = True
        self._prediction_lock = threading.Lock()
        self._last_requested_context = ""

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
        if keyval == IBus.Key.Tab and self._predictions:
            self._accept_prediction()
            return True

        # === DISMISS PREDICTION: Escape ===
        if keyval == IBus.Key.Escape and self._predictions:
            self._dismiss_predictions()
            return True

        # === BACKSPACE ===
        if keyval == IBus.Key.BackSpace:
            if self._preedit_text:
                self._preedit_text = self._preedit_text[:-1]
                self._context_buffer = self._context_buffer[:-1]
                self._update_preedit()
                self._trigger_prediction()
                return True
            return False

        # === ENTER / RETURN ===
        if keyval in (IBus.Key.Return, IBus.Key.KP_Enter):
            self._commit_preedit()
            self._context_buffer += "\n"
            self._clear_predictions()
            return False  # Let Enter pass through to the app

        # === SPACE ===
        if keyval == IBus.Key.space:
            self._commit_preedit()
            self._context_buffer += " "
            self._clear_predictions()
            return False  # Let space pass through

        # === REGULAR CHARACTER ===
        char = self._keyval_to_char(keyval)
        if char:
            self._preedit_text += char
            self._context_buffer += char
            self._update_preedit()
            self._trigger_prediction()
            return True

        return False

    def _keyval_to_char(self, keyval):
        """Convert IBus keyval to character."""
        if 0x20 <= keyval <= 0x7E:  # Printable ASCII
            return chr(keyval)
        return None

    def _update_preedit(self):
        """Update the preedit text shown in the input field."""
        if self._preedit_text:
            text = IBus.Text.new_from_string(self._preedit_text)
            attrs = IBus.AttrList()
            attrs.append(IBus.Attribute.new(
                IBus.AttrType.FOREGROUND,
                IBus.AttrUnderline.SINGLE,
                0, len(self._preedit_text),
                0x0000FF00,  # Green color
            ))
            text.set_attributes(attrs)
            self.update_preedit_text(text, len(self._preedit_text), True)
        else:
            self.update_preedit_text(IBus.Text.new_from_string(""), 0, False)

    def _commit_preedit(self):
        """Commit the preedit text to the application."""
        if self._preedit_text:
            text = IBus.Text.new_from_string(self._preedit_text)
            self.commit_text(text)
            self._preedit_text = ""
            self.update_preedit_text(IBus.Text.new_from_string(""), 0, False)

    def _trigger_prediction(self):
        """Request predictions from Gemini in a background thread."""
        if len(self._context_buffer.strip()) < self.config.min_buffer_length:
            return

        # Snapshot context under lock to avoid race condition
        with self._prediction_lock:
            context_snapshot = self._context_buffer

        # Skip if same context as last request (deduplicate)
        if context_snapshot == self._last_requested_context:
            return
        self._last_requested_context = context_snapshot

        # Run prediction in background to avoid blocking UI
        thread = threading.Thread(target=self._fetch_predictions, args=(context_snapshot,), daemon=True)
        thread.start()

    def _fetch_predictions(self, context):
        """Fetch predictions from Gemini (runs in background thread)."""
        try:
            predictions = self.predictor.get_predictions(context)
            with self._prediction_lock:
                self._predictions = predictions
            # Schedule UI update on main thread
            GLib.idle_add(self._show_predictions)
        except Exception as e:
            logger.error(f"Prediction error: {e}")

    def _show_predictions(self):
        """Display predictions in the IBus auxiliary text panel."""
        if not self._predictions:
            self.hide_auxiliary_text()
            return False

        # Build prediction display text
        pred_display = "  |  ".join(
            f"[{i+1}] {p}" for i, p in enumerate(self._predictions)
        )
        text = IBus.Text.new_from_string(f"  🪄 {pred_display}  [Tab]")

        attrs = IBus.AttrList()
        attrs.append(IBus.Attribute.new(
            IBus.AttrType.FOREGROUND,
            IBus.AttrUnderline.NONE,
            0, len(text.get_text()),
            0x00AAAAAA,  # Gray color
        ))
        text.set_attributes(attrs)

        self.update_auxiliary_text(text, True)
        self.show_auxiliary_text()
        return False  # Remove from GLib idle queue

    def _accept_prediction(self):
        """Accept the top prediction and insert it."""
        with self._prediction_lock:
            if not self._predictions:
                return
            prediction = self._predictions[0]

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
        with self._prediction_lock:
            self._predictions = []
        self.predictor.clear_cache()
        self.hide_auxiliary_text()

    def do_focus_in(self):
        """Called when an input field gains focus."""
        self._is_active = True
        logger.debug("Focus in")

    def do_focus_out(self):
        """Called when an input field loses focus."""
        self._is_active = False
        self._clear_predictions()
        logger.debug("Focus out")

    def do_reset(self):
        """Reset the engine state."""
        self._preedit_text = ""
        self._context_buffer = ""
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


class MindFlowEngineFactory:
    """Factory for creating MindFlow engine instances."""

    def __init__(self, bus=None):
        self._bus = bus

    def create_engine(self, engine_name):
        """Create and return a MindFlow engine instance."""
        if engine_name == ENGINE_NAME:
            return MindFlowEngine()
        return None


def main():
    """Main entry point for the IBus engine."""
    logger.info("Starting MindFlow IBus engine...")

    bus = IBus.Bus()

    if not bus.is_connected():
        logger.error("Cannot connect to IBus daemon!")
        sys.exit(1)

    # Create component
    component = IBus.Component(
        name="org.freedesktop.IBus.MindFlow",
        description="MindFlow AI Autocomplete Engine",
        version="0.1.0",
        license_="MIT",
        author="Seemoo",
        homepage="https://github.com/seemoo/mindflow",
        command_line="mindflow-engine",
        textdomain="mindflow",
    )

    # Add engine to component
    engine_desc = IBus.EngineDesc(
        name=ENGINE_NAME,
        longname=ENGINE_LONG_NAME,
        description=ENGINE_DESCRIPTION,
        language="en",
        license_="MIT",
        author="Seemoo",
        icon="input-keyboard",
        layout="us",
    )
    component.add_engine(engine_desc)

    # Create factory and register
    factory = IBus.Factory.new(bus.get_connection())
    factory.add_engine(ENGINE_NAME, GLib.Variant("s", ENGINE_NAME))

    # Register component
    bus.register_component(component)

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
