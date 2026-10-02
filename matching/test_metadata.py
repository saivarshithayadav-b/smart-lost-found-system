from matching.metadata_match import match_metadata


# TEST 1 — PERFECT MATCH

lost_item = {
    "category": "Mobile",
    "color": "Black",
    "brand": "Samsung",
    "lost_date": "2026-09-20"
}

found_item = {
    "category": "Mobile",
    "color": "Black",
    "brand": "Samsung",
    "found_date": "2026-09-20"
}

result = match_metadata(lost_item, found_item)

print("\nTEST 1 — Perfect Match")
print(result)


# TEST 2 — DIFFERENT BRAND

found_item["brand"] = "Apple"

result = match_metadata(lost_item, found_item)

print("\nTEST 2 — Different Brand")
print(result)


# TEST 3 — ONE DAY DATE DIFFERENCE

found_item["brand"] = "Samsung"
found_item["found_date"] = "2026-09-21"

result = match_metadata(lost_item, found_item)

print("\nTEST 3 — One Day Date Difference")
print(result)


# TEST 4 — DIFFERENT EVERYTHING

found_item = {
    "category": "Wallet",
    "color": "Brown",
    "brand": "Nike",
    "found_date": "2026-10-01"
}

result = match_metadata(lost_item, found_item)

print("\nTEST 4 — Different Everything")
print(result)
