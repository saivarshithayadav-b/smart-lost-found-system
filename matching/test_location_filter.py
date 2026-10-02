from matching.location_filter import (
    calculate_distance,
    filter_by_location
)


print("\n==============================")
print("LOCATION FILTER TEST")
print("==============================")


# Test 1 — Distance calculation

distance = calculate_distance(
    16.5062,
    80.6480,
    16.5065,
    80.6485
)

print("\nTest 1 — Distance")
print("Distance:", distance, "km")


# Test 2 — Nearby candidate

lost_item = {
    "latitude": 16.5062,
    "longitude": 80.6480
}


found_items = [
    {
        "id": 1,
        "item_name": "Blue Bag",
        "latitude": 16.5065,
        "longitude": 80.6485
    },
    {
        "id": 2,
        "item_name": "Black Wallet",
        "latitude": 17.0000,
        "longitude": 81.0000
    }
]


nearby_items = filter_by_location(
    lost_item,
    found_items,
    radius_km=5
)


print("\nTest 2 — Nearby Candidates")

print("Total found items:",
      len(found_items))

print("Nearby candidates:",
      len(nearby_items))


for item in nearby_items:

    print(
        "ID:",
        item["id"],
        "| Item:",
        item["item_name"],
        "| Distance:",
        item["distance_km"],
        "km"
    )