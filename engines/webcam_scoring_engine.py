"""
Webcam Scoring Engine
face-api.js runs in the browser and sends us clean floats.
We do NOT receive video frames — just pre-computed metrics.
"""

# Emotions that contribute to risk (not all emotions are equal)
RISK_EMOTIONS = {
    "fearful":   0.9,   # high weight — fear correlates with confusion
    "sad":       0.6,
    "angry":     0.5,
    "disgusted": 0.4,
    "surprised": 0.2,   # low weight — surprise is ambiguous
    "neutral":   0.0,
    "happy":    -0.1,   # slightly protective
}

def score_webcam(dominant_emotion: str, emotion_confidence: float,
                 avg_blink_rate: float, gaze_stability_score: float) -> float:
    """
    Returns a stress/risk score 0-100.
    Higher = more concern.
    """

    # Emotion risk — weighted by confidence
    emotion_risk = _calc_emotion_risk(dominant_emotion, emotion_confidence)

    # Blink rate — normal is 12-20 blinks/min
    # Under 8 = stress/intense concentration, over 30 = fatigue
    blink_risk = _calc_blink_risk(avg_blink_rate)

    # Gaze stability — high variance = erratic eye movement = attention difficulty
    gaze_risk = _calc_gaze_risk(gaze_stability_score)

    raw = emotion_risk + blink_risk + gaze_risk
    return max(0.0, min(100.0, raw))


def _calc_emotion_risk(emotion: str, confidence: float) -> float:
    """
    Maps dominant emotion to a risk weight, scaled by confidence.
    Max contribution: 40 points.
    """
    weight = RISK_EMOTIONS.get(emotion.lower(), 0.2)
    if weight <= 0:
        return 0.0
    return min(40.0, weight * confidence * 50)


def _calc_blink_risk(blink_rate: float) -> float:
    """
    Normal blink rate is 12-20/min.
    Abnormal rates in either direction are stress signals.
    Max contribution: 30 points.
    """
    if 12 <= blink_rate <= 20:
        return 0.0
    elif blink_rate < 8:
        return 25   # very low — stress/freeze
    elif blink_rate < 12:
        return 10
    elif blink_rate > 30:
        return 20   # high — fatigue
    elif blink_rate > 25:
        return 10
    return 0.0


def _calc_gaze_risk(stability_score: float) -> float:
    """
    Gaze stability is variance of X/Y eye position over session.
    Lower variance = more stable = lower risk.
    High variance = erratic = attention difficulty.
    Max contribution: 30 points.
    """
    if stability_score < 0.1:
        return 0.0
    elif stability_score < 0.3:
        return 8
    elif stability_score < 0.6:
        return 18
    else:
        return 30
