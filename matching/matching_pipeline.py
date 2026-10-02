from matching.metadata_match import match_metadata
from matching.text_match import text_similarity
from matching.image_match import image_similarity
from matching.score_fusion import calculate_final_score
from matching.match_decision import decide_match


def run_matching_pipeline(lost_item, found_item):
    """
    Run the complete AI matching pipeline.

    Steps:
        1. Metadata matching
        2. SBERT text matching
        3. CLIP image matching
        4. Score fusion
        5. Match decision
    """

    # 1. Metadata matching
    metadata_result = match_metadata(
        lost_item,
        found_item
    )

    metadata_score = metadata_result["metadata_score"]

    # 2. SBERT text matching
    text_score = text_similarity(
        lost_item.get("description"),
        found_item.get("description")
    )

    # 3. CLIP image matching
    image_score = 0.0

    lost_image = lost_item.get("image_path")
    found_image = found_item.get("image_path")

    if lost_image and found_image:
        image_score = image_similarity(
            lost_image,
            found_image
        )

    # 4. Score fusion
    final_score = calculate_final_score(
        metadata_score,
        text_score,
        image_score
    )

    # 5. Match decision
    decision_result = decide_match(
        final_score
    )

    # Return complete matching result
    return {
        "category_score": metadata_result["category_score"],
        "color_score": metadata_result["color_score"],
        "brand_score": metadata_result["brand_score"],
        "date_score": metadata_result["date_score"],
        "metadata_score": metadata_score,
        "text_score": text_score,
        "image_score": image_score,
        "final_score": final_score,
        "threshold": decision_result["threshold"],
        "decision": decision_result["decision"]
    }