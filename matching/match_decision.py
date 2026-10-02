# =========================================================
# MATCH DECISION
# =========================================================

# Initial testing threshold
MATCH_THRESHOLD = 0.70


def decide_match(final_score):
    """
    Decide whether two items are a potential match.

    Args:
        final_score: Combined score from score fusion.

    Returns:
        Dictionary containing the score, threshold,
        and match decision.
    """

    # -----------------------------------------------------
    # VALIDATE SCORE
    # -----------------------------------------------------

    try:
        final_score = float(final_score)
    except (TypeError, ValueError):
        final_score = 0.0

    # Keep score within 0–1
    final_score = max(
        0.0,
        min(1.0, final_score)
    )

    # -----------------------------------------------------
    # MATCH DECISION
    # -----------------------------------------------------

    if final_score >= MATCH_THRESHOLD:
        decision = "Potential Match"
    else:
        decision = "Not a Match"

    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {
        "final_score": round(
            final_score,
            4
        ),
        "threshold": MATCH_THRESHOLD,
        "decision": decision
    }