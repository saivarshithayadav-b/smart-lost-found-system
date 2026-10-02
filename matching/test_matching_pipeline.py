from matching.matching_pipeline import run_matching_pipeline


# =========================================================
# LOST ITEM
# =========================================================

lost_item = {
    "category": "Mobile",
    "color": "Black",
    "brand": "Samsung",
    "lost_date": "2026-09-20",

    "description":
        "Black Samsung phone with a cracked screen",

    "image_path":
        "uploads/Screenshot_2026-09-24_at_6.47.38_PM.png"
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
        "Samsung mobile, black color, damaged display",

    "image_path":
        "uploads/Screenshot_2026-09-24_at_7.02.55_PM.png"
}


# =========================================================
# RUN COMPLETE PIPELINE
# =========================================================

result = run_matching_pipeline(
    lost_item,
    found_item
)


# =========================================================
# DISPLAY RESULT
# =========================================================

print("\n==============================")
print("COMPLETE MATCHING PIPELINE")
print("==============================")

print("Category Score:",
      result["category_score"])

print("Color Score:",
      result["color_score"])

print("Brand Score:",
      result["brand_score"])

print("Date Score:",
      result["date_score"])

print("Metadata Score:",
      result["metadata_score"])

print("Text Score:",
      result["text_score"])

print("Image Score:",
      result["image_score"])

print("Final Score:",
      result["final_score"])

print("Threshold:",
      result["threshold"])

print("Decision:",
      result["decision"])