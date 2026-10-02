from matching.metadata_match import match_metadata
from matching.text_match import text_similarity
from matching.image_match import image_similarity
from matching.score_fusion import calculate_final_score
from matching.match_decision import decide_match


# =========================================================
# LOST ITEM
# =========================================================

lost_item = {
    "category": "Mobile",
    "color": "Black",
    "brand": "Samsung",
    "lost_date": "2026-09-20",

    "description":
        "Black Samsung phone with a cracked screen"
}


# =========================================================
# FOUND ITEM
# =========================================================

found_item = {
    "category": "Mobile",
    "color": "Black",
    "brand": "Samsung",
    "found_date": "2026-09-20",

    "description":
        "Samsung mobile, black color, damaged display"
}


# =========================================================
# IMAGE PATHS
# =========================================================

lost_image = (
    "uploads/"
    "Screenshot_2026-09-24_at_6.47.38_PM.png"
)

found_image = (
    "uploads/"
    "Screenshot_2026-09-24_at_7.02.55_PM.png"
)


# =========================================================
# STEP 1 — METADATA MATCHING
# =========================================================

metadata_result = match_metadata(
    lost_item,
    found_item
)

metadata_score = metadata_result["metadata_score"]

print("\n==============================")
print("STEP 1 — METADATA MATCHING")
print("==============================")

print("Category Score:",
      metadata_result["category_score"])

print("Color Score:",
      metadata_result["color_score"])

print("Brand Score:",
      metadata_result["brand_score"])

print("Date Score:",
      metadata_result["date_score"])

print("Metadata Score:",
      metadata_score)


# =========================================================
# STEP 2 — SBERT TEXT MATCHING
# =========================================================

text_score = text_similarity(
    lost_item["description"],
    found_item["description"]
)

print("\n==============================")
print("STEP 2 — SBERT TEXT MATCHING")
print("==============================")

print("Text Similarity Score:",
      text_score)


# =========================================================
# STEP 3 — CLIP IMAGE MATCHING
# =========================================================

image_score = image_similarity(
    lost_image,
    found_image
)

print("\n==============================")
print("STEP 3 — CLIP IMAGE MATCHING")
print("==============================")

print("Image Similarity Score:",
      image_score)


# =========================================================
# STEP 4 — SCORE FUSION
# =========================================================

final_score = calculate_final_score(
    metadata_score,
    text_score,
    image_score
)

print("\n==============================")
print("STEP 4 — SCORE FUSION")
print("==============================")

print("Metadata Score:",
      metadata_score)

print("Text Score:",
      text_score)

print("Image Score:",
      image_score)

print("Final Match Score:",
      final_score)


# =========================================================
# STEP 5 — MATCH DECISION
# =========================================================

decision = decide_match(
    final_score
)

print("\n==============================")
print("STEP 5 — MATCH DECISION")
print("==============================")

print("Final Score:",
      decision["final_score"])

print("Threshold:",
      decision["threshold"])

print("Decision:",
      decision["decision"])


# =========================================================
# FINAL RESULT
# =========================================================

print("\n==============================")
print("FINAL RESULT")
print("==============================")

print("Final Match Score:",
      decision["final_score"])

print("Final Decision:",
      decision["decision"])