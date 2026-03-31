"""
Chat Scoring Engine
Combines typing behaviour signals with TextBlob sentiment analysis.
The frontend computes WPM, delta, backspace rate — we just receive them.
We run TextBlob on the raw messages ourselves.
"""

from textblob import TextBlob


def score_chat(avg_wpm: float, wpm_delta: float, backspace_rate: float,
               repetition_count: int, messages: list) -> float:
    """
    Returns a risk score 0-100.
    Higher = more concern.
    """

    # WPM delta — declining speed is the strongest signal
    # Negative delta = user is slower than last session
    wpm_risk = _calc_wpm_risk(wpm_delta)

    # Backspace rate — high rate suggests confusion or self-correction
    backspace_risk = min(25, backspace_rate * 50)

    # Repetition — repeated phrases indicate memory loops
    repetition_risk = min(20, repetition_count * 7)

    # Sentiment — negative emotion amplifies risk
    sentiment_risk = _calc_sentiment_risk(messages)

    # Absolute WPM floor — very slow typists regardless of delta
    slow_penalty = _calc_slow_wpm_penalty(avg_wpm)

    raw = wpm_risk + backspace_risk + repetition_risk + sentiment_risk + slow_penalty
    return max(0.0, min(100.0, raw))


def _calc_wpm_risk(wpm_delta: float) -> float:
    """
    Negative delta means user is slower than last session.
    A drop of -5 WPM = 10 risk points. Max 30 points.
    """
    if wpm_delta >= 0:
        return 0.0
    return min(30.0, abs(wpm_delta) * 2)


def _calc_sentiment_risk(messages: list) -> float:
    """
    Run TextBlob polarity on the combined messages.
    Polarity: -1.0 (very negative) to +1.0 (very positive).
    Negative emotion = up to 15 extra risk points.
    """
    if not messages:
        return 0.0
    combined = " ".join(messages)
    try:
        polarity = TextBlob(combined).sentiment.polarity
        if polarity < 0:
            return min(15.0, abs(polarity) * 20)
        return 0.0
    except Exception:
        return 0.0


def _calc_slow_wpm_penalty(avg_wpm: float) -> float:
    """
    Absolute floor — very slow typists regardless of trend.
    Under 10 WPM is clinically notable for a chat conversation.
    """
    if avg_wpm < 5:
        return 15
    elif avg_wpm < 10:
        return 8
    return 0
