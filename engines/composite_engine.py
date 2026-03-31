"""
Composite Engine
Merges all 4 source scores into a single risk score.
Assigns clinical stage 0-3.
"""

# Source weights must sum to 1.0
WEIGHTS = {
    "game":  0.40,   # strongest signal — most structured
    "chat":  0.30,   # typing + sentiment
    "webcam": 0.20,  # emotion + blink + gaze
    "task":  0.10,   # daily habit signal
}


def score_daily(game_score: float, chat_score: float,
                webcam_score: float, task_completion_rate: float) -> float:
    """
    Returns composite risk score 0-100.
    task_completion_rate is 0.0-1.0 — we invert it (lower completion = higher risk).
    """
    task_risk = (1 - task_completion_rate) * 100

    composite = (
        game_score   * WEIGHTS["game"]  +
        chat_score   * WEIGHTS["chat"]  +
        webcam_score * WEIGHTS["webcam"] +
        task_risk    * WEIGHTS["task"]
    )
    return max(0.0, min(100.0, composite))


def get_stage(composite_score: float, trend_slope: float) -> tuple:
    """
    Returns (stage: int, explanation: str)
    Stage 0 = no concern
    Stage 1 = mild — monitor
    Stage 2 = moderate — recommend GP
    Stage 3 = high — urgent, triggers SMS

    trend_slope from trend_engine.calculate_trend():
    Positive = worsening over 7 days.
    """

    if composite_score < 25 and trend_slope < 0.3:
        return 0, (
            "No significant cognitive indicators detected. "
            "Continue daily activities and check in regularly."
        )

    elif composite_score < 45 or trend_slope < 0.5:
        return 1, (
            "Mild indicators observed. This may reflect a temporary off day. "
            "Monitor closely over the next week and maintain daily activities."
        )

    elif composite_score < 70 or trend_slope < 1.0:
        return 2, (
            "Moderate cognitive indicators detected across multiple sessions. "
            "We recommend discussing these results with a general practitioner."
        )

    else:
        return 3, (
            "High concern — consistent indicators detected across games, "
            "chat, and attention patterns. Please consult a neurologist. "
            "Your caregiver has been notified."
        )
