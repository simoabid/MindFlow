#!/usr/bin/env python3
"""Test script to verify MindFlow dependencies."""
import sys

def test_ibus():
    try:
        from gi.repository import IBus
        print("IBus OK")
        return True
    except Exception as e:
        print(f"IBus FAILED: {e}")
        return False

def test_gemini():
    try:
        from google import genai
        print("Gemini SDK OK")
        return True
    except Exception as e:
        print(f"Gemini SDK FAILED: {e}")
        return False

if __name__ == "__main__":
    results = [test_ibus(), test_gemini()]
    sys.exit(0 if all(results) else 1)
