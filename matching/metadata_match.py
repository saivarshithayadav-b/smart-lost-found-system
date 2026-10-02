from datetime import datetime


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(value):
    """
    Convert text into a consistent format
    for metadata comparison.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    # Replace common separators with spaces.
    value = value.replace("-", " ")
    value = value.replace("_", " ")

    # Remove extra spaces.
    value = " ".join(value.split())

    return value


# =========================================================
# BASIC METADATA MATCHING
# =========================================================

def text_match(value1, value2):
    """
    Compare two metadata values.

    Returns:
        1.0 -> exact normalized match
        0.0 -> no match
    """

    value1 = normalize_text(value1)
    value2 = normalize_text(value2)

    if not value1 or not value2:
        return 0.0

    return 1.0 if value1 == value2 else 0.0


# =========================================================
# DATE MATCHING
# =========================================================

def date_match(date1, date2):
    """
    Compare lost and found dates.

    Scoring:
        Same day -> 1.0
        1 day    -> 0.8
        2 days   -> 0.6
        3 days   -> 0.4
        4 days   -> 0.2
        5+ days  -> 0.0
    """

    if not date1 or not date2:
        return 0.0

    try:

        # Convert string dates.
        if isinstance(date1, str):
            date1 = datetime.strptime(
                date1[:10],
                "%Y-%m-%d"
            ).date()

        if isinstance(date2, str):
            date2 = datetime.strptime(
                date2[:10],
                "%Y-%m-%d"
            ).date()

        difference = abs(
            (date1 - date2).days
        )

        if difference == 0:
            return 1.0

        elif difference == 1:
            return 0.8

        elif difference == 2:
            return 0.6

        elif difference == 3:
            return 0.4

        elif difference == 4:
            return 0.2

        else:
            return 0.0

    except (ValueError, TypeError, AttributeError):
        return 0.0


# =========================================================
# METADATA MATCHING
# =========================================================

def match_metadata(lost_item, found_item):
    """
    Calculate metadata similarity using:

        Category -> 30%
        Color    -> 25%
        Brand    -> 25%
        Date     -> 20%

    Returns:
        Individual scores and combined metadata score.
    """

    # -----------------------------------------------------
    # CATEGORY
    # -----------------------------------------------------

    category_score = text_match(
        lost_item.get("category"),
        found_item.get("category")
    )

    # -----------------------------------------------------
    # COLOR
    # -----------------------------------------------------

    color_score = text_match(
        lost_item.get("color"),
        found_item.get("color")
    )

    # -----------------------------------------------------
    # BRAND
    # -----------------------------------------------------

    brand_score = text_match(
        lost_item.get("brand"),
        found_item.get("brand")
    )

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    date_score = date_match(
        lost_item.get("lost_date"),
        found_item.get("found_date")
    )

    # -----------------------------------------------------
    # WEIGHTS
    # -----------------------------------------------------

    category_weight = 0.30
    color_weight = 0.25
    brand_weight = 0.25
    date_weight = 0.20

    # -----------------------------------------------------
    # CALCULATE METADATA SCORE
    # -----------------------------------------------------

    metadata_score = (
        category_score * category_weight
        + color_score * color_weight
        + brand_score * brand_weight
        + date_score * date_weight
    )

    # -----------------------------------------------------
    # RETURN RESULTS
    # -----------------------------------------------------

    return {
        "category_score": round(
            category_score,
            4
        ),
        "color_score": round(
            color_score,
            4
        ),
        "brand_score": round(
            brand_score,
            4
        ),
        "date_score": round(
            date_score,
            4
        ),
        "metadata_score": round(
            metadata_score,
            4
        )
    }