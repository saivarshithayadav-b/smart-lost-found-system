from matching.score_fusion import calculate_final_score


# =====================================================
# TEST 1 — GOOD MATCH
# =====================================================

metadata_score = 0.75
text_score = 0.82
image_score = 0.80

final_score = calculate_final_score(
    metadata_score,
    text_score,
    image_score
)

print("\nTEST 1 — Good Match")
print("Metadata Score:", metadata_score)
print("Text Score:", text_score)
print("Image Score:", image_score)
print("Final Score:", final_score)


# =====================================================
# TEST 2 — PERFECT MATCH
# =====================================================

metadata_score = 1.0
text_score = 1.0
image_score = 1.0

final_score = calculate_final_score(
    metadata_score,
    text_score,
    image_score
)

print("\nTEST 2 — Perfect Match")
print("Final Score:", final_score)


# =====================================================
# TEST 3 — POOR MATCH
# =====================================================

metadata_score = 0.20
text_score = 0.15
image_score = 0.10

final_score = calculate_final_score(
    metadata_score,
    text_score,
    image_score
)

print("\nTEST 3 — Poor Match")
print("Final Score:", final_score)