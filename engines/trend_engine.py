"""
Trend Engine
Calculates 7-day slope of composite risk scores using numpy.polyfit.
Positive slope = worsening trend.
Tell judges: "longitudinal trajectory analysis"
"""

import numpy as np


def calculate_trend(daily_scores: list) -> float:
    """
    Takes a list of up to 7 daily composite scores (oldest first).
    Returns slope — positive means risk is increasing over time.

    Examples:
      [20, 22, 25, 30, 35, 40, 50] -> slope ~5.0  (worsening fast)
      [50, 45, 40, 38, 35, 32, 30] -> slope ~-3.0 (improving)
      [30, 31, 29, 32, 30, 31, 30] -> slope ~0.1  (stable)
    """
    if not daily_scores:
        return 0.0
    if len(daily_scores) < 3:
        # Not enough data for a meaningful trend
        return 0.0

    days = np.arange(len(daily_scores))
    slope = np.polyfit(days, daily_scores, 1)[0]
    return float(slope)


def get_trend_label(slope: float) -> str:
    """Human-readable trend label for dashboard."""
    if slope > 1.5:
        return "Worsening rapidly"
    elif slope > 0.5:
        return "Worsening"
    elif slope > -0.5:
        return "Stable"
    elif slope > -1.5:
        return "Improving"
    else:
        return "Improving rapidly"
