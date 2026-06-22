# tests/integration_test.py
"""Manual integration test — run this to verify the Gemini pipeline works."""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mindflow.predictor import Predictor
from mindflow.config import MindFlowConfig


def test_full_pipeline():
    """Test the full prediction pipeline."""
    config = MindFlowConfig.load()

    if not config.api_key:
        print("❌ No API key set! Edit ~/.config/mindflow/config.json")
        print('   Set "api_key": "YOUR_GEMINI_API_KEY"')
        sys.exit(1)

    predictor = Predictor(api_key=config.api_key, model=config.model)

    test_cases = [
        "The weather today is",
        "I need to go to the",
        "Python is a great programming",
        "Can you help me with",
    ]

    print("🧠 MindFlow Integration Test")
    print("=" * 50)

    passed = 0
    for context in test_cases:
        print(f"\n📝 Input: '{context}'")
        predictions = predictor.get_predictions(context)
        if predictions:
            for i, pred in enumerate(predictions, 1):
                print(f"   [{i}] {pred}")
            passed += 1
        else:
            print("   (no predictions)")
        predictor.clear_cache()

    print("\n" + "=" * 50)
    print(f"✅ {passed}/{len(test_cases)} test cases produced predictions")

    if passed == len(test_cases):
        print("🎉 All tests passed!")
    elif passed > 0:
        print("⚠️  Some tests produced no predictions (may be API rate limiting)")
    else:
        print("❌ No predictions returned — check your API key and network")
        sys.exit(1)


if __name__ == "__main__":
    test_full_pipeline()
