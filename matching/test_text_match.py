from matching.text_match import text_similarity


# ==========================================
# TEST 1 — VERY SIMILAR DESCRIPTIONS
# ==========================================

text1 = "Black Samsung phone with cracked screen"

text2 = "Samsung mobile, black color, damaged display"

score = text_similarity(text1, text2)

print("\nTEST 1 — Similar Descriptions")
print("Score:", score)


# ==========================================
# TEST 2 — SAME OBJECT, DIFFERENT WORDING
# ==========================================

text1 = "Blue school bag with two front pockets"

text2 = "A blue backpack having two pockets in the front"

score = text_similarity(text1, text2)

print("\nTEST 2 — Same Meaning")
print("Score:", score)


# ==========================================
# TEST 3 — COMPLETELY DIFFERENT ITEMS
# ==========================================

text1 = "Black Samsung phone with cracked screen"

text2 = "Brown leather wallet containing an ID card"

score = text_similarity(text1, text2)

print("\nTEST 3 — Different Items")
print("Score:", score)


# ==========================================
# TEST 4 — EXACT SAME DESCRIPTION
# ==========================================

text1 = "Red Nike shoes"

text2 = "Red Nike shoes"

score = text_similarity(text1, text2)

print("\nTEST 4 — Exact Same Text")
print("Score:", score)
