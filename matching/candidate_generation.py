from matching.candidate_search import get_found_candidates
from matching.location_filter import filter_by_location


def generate_candidates(
    lost_item,
    radius_km=5
):
    """
    Generate found-item candidates for a
    particular lost item.

    Steps:
        1. Retrieve found items from MySQL.
        2. Exclude found items uploaded by
           the same user who reported the lost item.
        3. Filter them using geographic distance.
        4. Return nearby candidates.
    """

    # Get the user who reported the lost item.
    lost_item_user_id = lost_item.get(
        "user_id"
    )

    # Retrieve found items belonging to
    # other users only.
    found_items = get_found_candidates(
        exclude_user_id=lost_item_user_id
    )

    # DEBUG: Show which user is being excluded.
    print(
        "DEBUG: Lost user ID =",
        lost_item_user_id
    )

    # DEBUG: Show the found items remaining
    # after excluding the same user's items.
    print(
        "DEBUG: Found candidates =",
        [
            (
                item["id"],
                item["user_id"],
                item["item_name"]
            )
            for item in found_items
        ]
    )

    # Apply the location filter.
    nearby_candidates = filter_by_location(
        lost_item,
        found_items,
        radius_km
    )

    return nearby_candidates