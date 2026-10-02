# =========================================================
# SCORE FUSION
# =========================================================

def calculate_final_score(
    metadata_score,
    text_score,
    image_score
):
    """
    Combine metadata, SBERT text, and CLIP image
    similarity scores into one final score.

    Current experimental weights:

        Metadata -> 30%
        Text    -> 35%
        Image   -> 35%

    Returns:
        Final score between 0.0 and 1.0
    """

    # -----------------------------------------------------
    # WEIGHTS
    # -----------------------------------------------------

    metadata_weight = 0.30
    text_weight = 0.35
    image_weight = 0.35

    # -----------------------------------------------------
    # CALCULATE FINAL SCORE
    # -----------------------------------------------------

    final_score = (
        metadata_score * metadata_weight
        + text_score * text_weight
        + image_score * image_weight
    )

    # -----------------------------------------------------
    # RETURN SCORE
    # -----------------------------------------------------

    return round(final_score, 4)