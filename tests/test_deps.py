#!/usr/bin/env python3
"""Verify MindFlow runtime dependencies are importable."""


def test_ibus_bindings_importable():
    import gi

    gi.require_version("IBus", "1.0")
    from gi.repository import IBus  # noqa: F401


def test_gemini_sdk_importable():
    from google import genai  # noqa: F401
