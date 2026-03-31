"""
Game Scoring Engine
Maps to: Memory Mosaic, Word Garden, Path Finder
Clinically inspired by: Hopkins Verbal Learning Test, MoCA verbal fluency, Trail Making Test B
"""

def score_game(test_type: str, score: float, time_taken_ms: int,
               errors: int, hesitation_gaps: list, age: int) -> float:
    """
    Returns a risk score 0-100.
    Higher = more concern.
    """

    # Convert accuracy to base risk (inverse — low accuracy = high risk)
    base_risk = (1 - score) * 100

    # Age adjustment — older users get a scoring curve
    age_multiplier = _get_age_multiplier(age)

    # Hesitation gap penalty — long pauses between taps indicate retrieval difficulty
    hesitation_penalty = _calc_hesitation_penalty(hesitation_gaps)

    # Error penalty
    error_penalty = min(30, errors * 5)

    # Time penalty — very slow completion
    time_penalty = _calc_time_penalty(time_taken_ms, test_type)

    raw = (base_risk * age_multiplier) + hesitation_penalty + error_penalty + time_penalty
    return max(0.0, min(100.0, raw))


def _get_age_multiplier(age: int) -> float:
    """Older users get their score curved upward (less penalised for same errors)."""
    if age < 65:
        return 1.0
    elif age < 75:
        return 0.85
    else:
        return 0.75


def _calc_hesitation_penalty(gaps: list) -> float:
    """
    Long pauses between taps = retrieval difficulty.
    A gap >2000ms gets full penalty per occurrence.
    Max penalty: 25 points.
    """
    if not gaps:
        return 0.0
    avg_gap = sum(gaps) / len(gaps)
    long_gaps = sum(1 for g in gaps if g > 2000)
    avg_penalty = min(15, avg_gap / 400)        # avg gap contributes up to 15pts
    long_penalty = min(10, long_gaps * 3)       # each freeze contributes 3pts, max 10
    return avg_penalty + long_penalty


def _calc_time_penalty(time_ms: int, test_type: str) -> float:
    """
    Penalise very slow completion relative to expected time.
    Expected times (ms): memory=60000, word=90000, path=120000
    """
    expected = {
        "memory_mosaic": 60_000,
        "word_garden": 90_000,
        "path_finder": 120_000
    }.get(test_type, 90_000)

    ratio = time_ms / expected
    if ratio > 2.5:
        return 15   # took more than 2.5x expected — significant
    elif ratio > 1.5:
        return 7
    return 0
