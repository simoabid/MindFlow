# mindflow/providers/base.py
"""Provider interface for text-prediction backends."""

from __future__ import annotations

import abc


class PredictionProvider(abc.ABC):
    """Abstract backend that turns a context string into ranked predictions.

    Implementations must be safe to call from a background thread and must
    never raise: errors are swallowed and reported as an empty prediction list
    so the input method never blocks the user's typing.
    """

    #: Stable identifier used in config and diagnostics.
    name: str = "base"

    @abc.abstractmethod
    def predict(self, context: str) -> list[str]:
        """Return ranked predictions (most likely first) for ``context``."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can currently serve predictions."""

    def describe(self) -> str:
        """Human-readable one-line status for diagnostics."""
        state = "ready" if self.is_available() else "unavailable"
        return f"{self.name} ({state})"

    def learn(self, text: str) -> None:  # noqa: B027 - intentional no-op hook
        """Optional hook to learn from accepted text. Default: do nothing."""
