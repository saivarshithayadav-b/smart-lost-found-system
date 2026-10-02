from math import radians, sin, cos, sqrt, atan2


def calculate_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):
    """
    Calculate the distance between two
    geographic coordinates using the
    Haversine formula.

    Returns:
        Distance in kilometers.
        Returns None if coordinates are invalid.
    """

    # -----------------------------------------------------
    # CHECK FOR MISSING VALUES
    # -----------------------------------------------------

    if (
        latitude1 is None
        or longitude1 is None
        or latitude2 is None
        or longitude2 is None
    ):
        return None

    # -----------------------------------------------------
    # CONVERT COORDINATES TO FLOAT
    # -----------------------------------------------------

    try:
        latitude1 = float(latitude1)
        longitude1 = float(longitude1)
        latitude2 = float(latitude2)
        longitude2 = float(longitude2)
    except (ValueError, TypeError):
        return None

    # -----------------------------------------------------
    # VALIDATE COORDINATE RANGES
    # -----------------------------------------------------

    if not (-90 <= latitude1 <= 90):
        return None

    if not (-90 <= latitude2 <= 90):
        return None

    if not (-180 <= longitude1 <= 180):
        return None

    if not (-180 <= longitude2 <= 180):
        return None

    # -----------------------------------------------------
    # EARTH RADIUS
    # -----------------------------------------------------

    earth_radius = 6371.0

    # -----------------------------------------------------
    # CONVERT DEGREES TO RADIANS
    # -----------------------------------------------------

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)

    difference_latitude = radians(
        latitude2 - latitude1
    )

    difference_longitude = radians(
        longitude2 - longitude1
    )

    # -----------------------------------------------------
    # HAVERSINE FORMULA
    # -----------------------------------------------------

    a = (
        sin(difference_latitude / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(difference_longitude / 2) ** 2
    )

    # Protect against tiny floating-point errors.
    a = max(0.0, min(1.0, a))

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    distance = earth_radius * c

    return round(distance, 4)


def filter_by_location(
    lost_item,
    found_items,
    radius_km=5
):
    """
    Keep found items that are within
    the specified radius of a lost item.

    Returns:
        List of nearby found items.
    """

    nearby_items = []

    # -----------------------------------------------------
    # GET LOST ITEM LOCATION
    # -----------------------------------------------------

    lost_latitude = lost_item.get(
        "latitude"
    )

    lost_longitude = lost_item.get(
        "longitude"
    )

    # -----------------------------------------------------
    # CHECK EACH FOUND ITEM
    # -----------------------------------------------------

    for found_item in found_items:

        distance = calculate_distance(
            lost_latitude,
            lost_longitude,
            found_item.get("latitude"),
            found_item.get("longitude")
        )

        # -------------------------------------------------
        # KEEP ONLY ITEMS WITHIN RADIUS
        # -------------------------------------------------

        if (
            distance is not None
            and distance <= radius_km
        ):

            found_item = found_item.copy()

            found_item["distance_km"] = distance

            nearby_items.append(
                found_item
            )

    return nearby_items