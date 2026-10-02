from matching.match_decision import decide_match


# =====================================================
# TEST 1 — HIGH SCORE
# =====================================================

final_score = 0.85

result = decide_match(final_score)

print("\nTEST 1 — High Score")
print(result)


# =====================================================
# TEST 2 — EXACTLY AT THRESHOLD
# =====================================================

final_score = 0.70

result = decide_match(final_score)

print("\nTEST 2 — Exactly At Threshold")
print(result)


# =====================================================
# TEST 3 — LOW SCORE
# =====================================================

final_score = 0.45

result = decide_match(final_score)

print("\nTEST 3 — Low Score")
print(result)


# =====================================================
# TEST 4 — PERFECT SCORE
# =====================================================

final_score = 1.0

result = decide_match(final_score)

print("\nTEST 4 — Perfect Score")
print(result)