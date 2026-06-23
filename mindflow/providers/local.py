# mindflow/providers/local.py
"""Offline prediction provider backed by a lightweight n-gram language model.

This provider needs no network and no API key. It seeds a small bigram/trigram
model from a built-in English corpus and keeps learning from the text the user
accepts, so MindFlow degrades gracefully (and privately) when Gemini is
unavailable or the user opts out of the cloud.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from collections import Counter, defaultdict
from pathlib import Path

from ..constants import MAX_PREDICTIONS, MAX_SUGGESTION_WORDS, PROVIDER_LOCAL
from .base import PredictionProvider

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[A-Za-z']+")

# Bound on-disk learned history so accepted text isn't retained indefinitely.
MAX_HISTORY_LINES = 500

# A compact but varied seed corpus so the model produces useful suggestions
# out of the box, before it has learned anything from the user.
SEED_CORPUS = """
Thank you for your email and for reaching out to me today.
I am writing to let you know that the meeting has been rescheduled.
Please let me know if you have any questions or concerns.
Looking forward to hearing from you soon.
I hope this message finds you well and in good health.
Let me know what works best for your schedule this week.
I wanted to follow up on our conversation from yesterday.
Could you please send me the latest version of the document.
I will get back to you as soon as possible with an update.
Thanks again for your help and your patience with this issue.
The quick brown fox jumps over the lazy dog every morning.
Python is a great programming language for building software quickly.
We should schedule a call to discuss the project requirements in detail.
I appreciate your time and look forward to working together with you.
Have a great day and please reach out if you need anything else.
Let me know if that works for you or if you would prefer another time.
I think we should focus on the most important features first.
The weather today is sunny with a gentle breeze and clear skies.
I need to go to the store later to pick up a few things.
Can you help me with this problem when you get a chance.
"""


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class LocalProvider(PredictionProvider):
    """A self-contained n-gram autocomplete model."""

    name = PROVIDER_LOCAL

    def __init__(
        self,
        max_predictions: int = MAX_PREDICTIONS,
        max_suggestion_words: int = MAX_SUGGESTION_WORDS,
        history_path: str | Path | None = None,
    ):
        self.max_predictions = max(1, int(max_predictions))
        self.max_suggestion_words = max(1, int(max_suggestion_words))
        self._history_path = Path(history_path) if history_path else None

        self._unigram: Counter[str] = Counter()
        self._bigram: dict[str, Counter[str]] = defaultdict(Counter)
        self._trigram: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        self._vocab: set[str] = set()
        self._learned_text: list[str] = []
        # predict() runs on a background thread while learn() runs on the main
        # GLib thread; guard the shared n-gram tables so a reader never iterates
        # a structure that a writer is mutating.
        self._lock = threading.Lock()

        self._train(SEED_CORPUS)
        self._load_history()

    # ------------------------------------------------------------------ training
    def _train(self, text: str) -> None:
        tokens = _tokenize(text)
        self._unigram.update(tokens)
        self._vocab.update(tokens)
        for i in range(len(tokens) - 1):
            self._bigram[tokens[i]][tokens[i + 1]] += 1
        for i in range(len(tokens) - 2):
            self._trigram[(tokens[i], tokens[i + 1])][tokens[i + 2]] += 1

    def learn(self, text: str) -> None:
        if not text or not text.strip():
            return
        with self._lock:
            self._train(text)
            self._learned_text.append(text.strip())
            # Keep only the most recent lines so we don't retain accepted text
            # (which may be sensitive) without bound.
            if len(self._learned_text) > MAX_HISTORY_LINES:
                self._learned_text = self._learned_text[-MAX_HISTORY_LINES:]
        self._save_history()

    # --------------------------------------------------------------- prediction
    def predict(self, context: str) -> list[str]:
        if not context or not context.strip():
            return []

        ends_with_space = context[-1].isspace()
        tokens = _tokenize(context)
        if not tokens:
            return []

        with self._lock:
            if ends_with_space:
                seeds = self._next_word_candidates(tokens)
                prefix = ""
            else:
                # The last token is a word still being typed: complete it.
                partial = tokens[-1]
                history = tokens[:-1]
                seeds = self._completion_candidates(partial, history)
                prefix = partial

            predictions: list[str] = []
            seen: set[str] = set()
            for first_word, _ in seeds:
                phrase = self._extend_phrase(tokens, first_word, prefix, ends_with_space)
                key = phrase.lower()
                if phrase and key not in seen:
                    seen.add(key)
                    predictions.append(phrase)
                if len(predictions) >= self.max_predictions:
                    break
        return predictions

    def _next_word_candidates(self, tokens: list[str]) -> list[tuple[str, int]]:
        if len(tokens) >= 2:
            tri = self._trigram.get((tokens[-2], tokens[-1]))
            if tri:
                return self._rank(tri)
        bi = self._bigram.get(tokens[-1])
        if bi:
            return self._rank(bi)
        return self._rank(self._unigram)

    def _completion_candidates(self, partial: str, history: list[str]) -> list[tuple[str, int]]:
        # Prefer words that both fit the n-gram context and start with the prefix.
        context_counts: Counter[str] = Counter()
        if history:
            if len(history) >= 2:
                context_counts.update(self._trigram.get((history[-2], history[-1]), Counter()))
            context_counts.update(self._bigram.get(history[-1], Counter()))

        matches = {
            w: c for w, c in context_counts.items() if w.startswith(partial) and w != partial
        }
        if matches:
            return self._rank(Counter(matches))

        # Fall back to the most frequent vocabulary words sharing the prefix.
        vocab_matches = Counter(
            {w: self._unigram[w] for w in self._vocab if w.startswith(partial) and w != partial}
        )
        return self._rank(vocab_matches)

    def _extend_phrase(
        self, context_tokens: list[str], first_word: str, prefix: str, ends_with_space: bool
    ) -> str:
        """Greedily grow a phrase starting at ``first_word`` up to the word limit."""
        if ends_with_space:
            history = context_tokens[:]
            words = [first_word]
        else:
            history = context_tokens[:-1]
            words = [first_word]

        while len(words) < self.max_suggestion_words:
            w1 = (history + words)[-2] if len(history + words) >= 2 else None
            w2 = (history + words)[-1]
            nxt = None
            if w1 is not None:
                tri = self._trigram.get((w1, w2))
                if tri:
                    nxt = tri.most_common(1)[0][0]
            if nxt is None:
                bi = self._bigram.get(w2)
                if bi:
                    nxt = bi.most_common(1)[0][0]
            if nxt is None or nxt in words:
                break
            words.append(nxt)

        return " ".join(words)

    @staticmethod
    def _rank(counter: Counter[str]) -> list[tuple[str, int]]:
        # Deterministic ordering: count desc, then alphabetical.
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))

    def is_available(self) -> bool:
        return bool(self._vocab)

    def describe(self) -> str:
        return f"{self.name} (vocab={len(self._vocab)} words, offline)"

    # ----------------------------------------------------------------- history
    def _load_history(self) -> None:
        if not self._history_path or not self._history_path.exists():
            return
        try:
            with open(self._history_path, encoding="utf-8") as f:
                data = json.load(f)
            lines = data.get("lines", [])
            if isinstance(lines, list):
                self._learned_text = [str(line) for line in lines][-MAX_HISTORY_LINES:]
                for line in self._learned_text:
                    self._train(line)
        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.debug("Could not load local history: %s", e)

    def _save_history(self) -> None:
        if not self._history_path:
            return
        # Persist the raw accepted lines and retrain on load. This keeps the
        # file human-readable and avoids serialising large nested counters.
        # Written owner-only (0600) since accepted text may be sensitive.
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(self._history_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"lines": self._learned_text}, f, indent=2)
            try:
                os.chmod(self._history_path, 0o600)
            except OSError as e:  # pragma: no cover - platform dependent
                logger.debug("Could not set permissions on local history: %s", e)
        except OSError as e:
            logger.debug("Could not persist local history: %s", e)
