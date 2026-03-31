"""
Quick test script — run this to verify all engines work before starting the server.
Does NOT need the server running. Tests engines directly.

Usage:
  python test_endpoints.py
"""

from engines.game_scoring_engine import score_game
from engines.chat_scoring_engine import score_chat
from engines.webcam_scoring_engine import score_webcam
from engines.composite_engine import score_daily, get_stage
from engines.trend_engine import calculate_trend, get_trend_label


def test_game():
    print("\n── Game Engine ──────────────────────────────")
    # Healthy user: high score, no hesitation, no errors
    healthy = score_game("memory_mosaic", 0.9, 45000, 0, [300, 250, 400], 60)
    print(f"  Healthy (0.9 score, age 60):   {healthy:.1f}")

    # Concerning: low score, long hesitation gaps, errors
    concern = score_game("path_finder", 0.4, 180000, 5, [400, 3500, 2800, 4000], 75)
    print(f"  Concern (0.4 score, age 75):   {concern:.1f}")

    assert healthy < concern, "Healthy should score lower than concern"
    print("  PASS")


def test_chat():
    print("\n── Chat Engine ──────────────────────────────")
    healthy_msgs = ["I had a lovely morning today", "The weather is nice", "I called my daughter"]
    concern_msgs = ["I forgot what I was saying", "I don't know I don't know", "Everything feels wrong"]

    healthy = score_chat(45.0, +2.0, 0.05, 0, healthy_msgs)
    concern = score_chat(18.0, -12.0, 0.35, 3, concern_msgs)
    print(f"  Healthy: {healthy:.1f}   Concern: {concern:.1f}")

    assert healthy < concern
    print("  PASS")


def test_webcam():
    print("\n── Webcam Engine ────────────────────────────")
    healthy = score_webcam("happy", 0.85, 15.0, 0.08)
    concern = score_webcam("fearful", 0.75, 4.0, 0.72)
    print(f"  Healthy: {healthy:.1f}   Concern: {concern:.1f}")

    assert healthy < concern
    print("  PASS")


def test_composite():
    print("\n── Composite Engine ─────────────────────────")
    composite = score_daily(65.0, 70.0, 55.0, 0.4)
    stage, explanation = get_stage(composite, 0.9)
    print(f"  Composite: {composite:.1f}  Stage: {stage}")
    print(f"  Explanation: {explanation[:60]}...")
    print("  PASS")


def test_trend():
    print("\n── Trend Engine ─────────────────────────────")
    worsening = calculate_trend([20, 25, 32, 38, 45, 52, 60])
    stable    = calculate_trend([30, 31, 29, 32, 30, 31, 30])
    improving = calculate_trend([60, 52, 44, 38, 32, 26, 20])

    print(f"  Worsening slope: {worsening:.2f} — {get_trend_label(worsening)}")
    print(f"  Stable slope:    {stable:.2f} — {get_trend_label(stable)}")
    print(f"  Improving slope: {improving:.2f} — {get_trend_label(improving)}")

    assert worsening > 0
    assert improving < 0
    print("  PASS")


if __name__ == "__main__":
    print("CogniScreen ML Engine Tests")
    print("="*48)
    try:
        test_game()
        test_chat()
        test_webcam()
        test_composite()
        test_trend()
        print("\n" + "="*48)
        print("All tests passed. Safe to start server.")
        print("  uvicorn main:app --reload --port 8000")
        print("="*48 + "\n")
    except AssertionError as e:
        print(f"\nFAILED: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
