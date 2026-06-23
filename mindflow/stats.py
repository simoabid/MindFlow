# mindflow/stats.py
"""Local, privacy-preserving usage statistics.

Counters only — no typed text is ever recorded. Stored as JSON under the XDG
state directory so they survive restarts. All operations are best-effort and
never raise into the engine.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from .constants import STATS_FILE

logger = logging.getLogger(__name__)


@dataclass
class Stats:
    """Aggregate counters describing MindFlow usage."""

    predictions_requested: int = 0
    predictions_shown: int = 0
    suggestions_accepted: int = 0
    suggestions_dismissed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def acceptance_rate(self) -> float:
        if self.predictions_shown == 0:
            return 0.0
        return self.suggestions_accepted / self.predictions_shown


class StatsTracker:
    """Loads, mutates and persists :class:`Stats`."""

    def __init__(self, path: str | Path | None = None, enabled: bool = True):
        self.path = Path(path) if path else STATS_FILE
        self.enabled = enabled
        # Counters are incremented from both the GLib main thread and the
        # background prediction thread, so guard the read-modify-write.
        self._lock = threading.Lock()
        self.stats = self._load()

    def _load(self) -> Stats:
        if not self.path.exists():
            return Stats()
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            valid = {f.name for f in fields(Stats)}
            return Stats(**{k: int(v) for k, v in data.items() if k in valid})
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.debug("Could not load stats (%s); starting fresh", e)
            return Stats()

    def save(self) -> None:
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Owner-only perms, consistent with config/history files.
            with self._lock:
                snapshot = asdict(self.stats)
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
            try:
                os.chmod(self.path, 0o600)
            except OSError as e:  # pragma: no cover - platform dependent
                logger.debug("Could not set permissions on stats file: %s", e)
        except OSError as e:
            logger.debug("Could not persist stats: %s", e)

    def increment(self, field_name: str, amount: int = 1) -> None:
        if not self.enabled:
            return
        if not hasattr(self.stats, field_name):
            return
        with self._lock:
            setattr(self.stats, field_name, getattr(self.stats, field_name) + amount)

    def reset(self) -> None:
        self.stats = Stats()
        self.save()
