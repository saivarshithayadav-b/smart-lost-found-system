from matching.candidate_generation import generate_candidates


# Real lost item from MySQL
lost_item = {
    "id": 7,
    "item_name": "Blue Bag",
    "category": "Bag",
    "latitude": 16.52618756,
    "longitude": 80.65114122
}


candidates = generate_candidates(
    lost_item,
    radius_km=5
)


print("\n==============================")
print("REAL CANDIDATE GENERATION TEST")
print("==============================")

print("Lost Item:",
      lost_item["item_name"])

print("Lost Latitude:",
      lost_item["latitude"])

print("Lost Longitude:",
      lost_item["longitude"])

print("Search Radius:",
      "5 km")

print("\nNearby Candidates:",
      len(candidates))


for candidate in candidates:

    print("\n------------------------------")

    print("Found ID:",
          candidate["id"])

    print("Item:",
          candidate["item_name"])

    print("Category:",
          candidate["category"])

    print("Color:",
          candidate["color"])

    print("Brand:",
          candidate["brand"])

    print("Location:",
          candidate["location"])

    print("Latitude:",
          candidate["latitude"])

    print("Longitude:",
          candidate["longitude"])

    print("Distance:",
          candidate["distance_km"],
          "km")