import os

from matching.candidate_generation import generate_candidates
from matching.matching_pipeline import run_matching_pipeline


def prepare_image_path(image_path):
    """
    Convert the image filename stored in MySQL
    into the actual path inside the uploads folder.

    Example:

    Database:
        photo.png

    Actual file:
        uploads/photo.png
    """

    if not image_path:
        return None

    return os.path.join(
        "uploads",
        image_path
    )


def match_lost_item(lost_item, radius_km=5):
    """
    Find nearby found-item candidates for a lost item
    and run the complete AI matching pipeline.

    Steps:

        1. Generate nearby candidates.
        2. Prepare image paths.
        3. Run metadata matching.
        4. Run SBERT text matching.
        5. Run CLIP image matching.
        6. Fuse all scores.
        7. Make the final match decision.

    Returns:
        A list of matching results sorted by final score.
    """

    # Step 1:
    # Find nearby found items using location.
    candidates = generate_candidates(
        lost_item,
        radius_km
    )

    results = []

    # Step 2:
    # Process every nearby candidate.
    for candidate in candidates:

        # Make copies so that we don't modify
        # the original database records.
        lost_item_for_ai = lost_item.copy()
        found_item_for_ai = candidate.copy()

        # Step 3:
        # Convert database image filenames
        # into paths inside the uploads folder.
        lost_item_for_ai["image_path"] = (
            prepare_image_path(
                lost_item_for_ai.get("image_path")
            )
        )

        found_item_for_ai["image_path"] = (
            prepare_image_path(
                found_item_for_ai.get("image_path")
            )
        )

        # Step 4:
        # Run metadata + SBERT + CLIP + score fusion.
        result = run_matching_pipeline(
            lost_item_for_ai,
            found_item_for_ai
        )

        # Add information about the candidate.
        result["found_item_id"] = candidate["id"]

        result["found_item_name"] = (
            candidate["item_name"]
        )

        result["distance_km"] = (
            candidate["distance_km"]
        )

        # Add original image filenames.
        # These are used by match_results.html
        # to display the two images.
        result["lost_item_image"] = (
            lost_item.get("image_path")
        )

        result["found_item_image"] = (
            candidate.get("image_path")
        )

        results.append(result)

    # Step 5:
    # Highest scoring candidate first.
    results.sort(
        key=lambda item: item["final_score"],
        reverse=True
    )

    return results