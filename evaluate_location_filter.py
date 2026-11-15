
import time

from database import get_db_connection
from matching.candidate_search import get_found_candidates
from matching.location_filter import filter_by_location

RADIUS = 5
POSITIVE_PAIRS = {
    (33, 27),
    (20, 13),
    (21, 14),
    (22, 17)
}

conn = get_db_connection()
cur = conn.cursor(dictionary=True)

cur.execute("SELECT * FROM lost_items ORDER BY id")
lost_items = cur.fetchall()

cur.close()
conn.close()

before = 0
after = 0
total_time = 0
runs = 0
retained = set()
missing_lost = 0
missing_found = 0

for lost in lost_items:
    candidates = get_found_candidates(
        exclude_user_id=lost.get("user_id")
    )

    before += len(candidates)

    if lost.get("latitude") is None or lost.get("longitude") is None:
        missing_lost += 1

    missing_found += sum(
        item.get("latitude") is None or item.get("longitude") is None
        for item in candidates
    )

    start = time.perf_counter()

    nearby = filter_by_location(
        lost,
        candidates,
        RADIUS
    )

    elapsed = (time.perf_counter() - start) * 1000

    total_time += elapsed
    runs += 1
    after += len(nearby)

    for item in nearby:
        pair = (lost["id"], item["id"])
        if pair in POSITIVE_PAIRS:
            retained.add(pair)

avg_time = total_time / runs if runs else 0
reduction = ((before - after) / before * 100) if before else 0

print("\nLOCATION FILTERING EXPERIMENT")
print("-" * 55)
print(f"Lost reports tested:              {len(lost_items)}")
print(f"Candidate reports before filter:  {before}")
print(f"Candidate reports after filter:   {after}")
print(f"Candidate reduction:              {reduction:.2f}%")
print(f"Genuine matches retained:         {len(retained)}")
print(f"Filtering radius:                 {RADIUS} km")
print(f"Total filtering time:             {total_time:.4f} ms")
print(f"Average filtering time:           {avg_time:.4f} ms")
print(f"Lost reports missing coordinates: {missing_lost}")
print(f"Candidate records missing coords: {missing_found}")
print(f"Retained positive pairs:          {sorted(retained)}")
print("-" * 55)
