from matching.candidate_search import get_found_candidates


candidates = get_found_candidates()


print("\n==============================")
print("FOUND ITEM CANDIDATES")
print("==============================")

print("Total candidates:", len(candidates))

for candidate in candidates:
    print("\nID:", candidate["id"])
    print("Item:", candidate["item_name"])
    print("Category:", candidate["category"])
    print("Color:", candidate["color"])
    print("Brand:", candidate["brand"])
    print("Location:", candidate["location"])
    print("Image:", candidate["image_path"])