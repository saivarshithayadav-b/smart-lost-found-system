import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

df = pd.read_csv("table_4_2_evaluation_pairs.csv")

y = df["actual_match"]
s = df["metadata_sbert_clip_score"]

print("\nTABLE 4.3: THRESHOLD EXPERIMENT RESULTS")
print("-" * 65)
print(f"{'Threshold':<12}{'Precision':<15}{'Recall':<15}{'F1-score':<15}")
print("-" * 65)

for t in [0.50, 0.60, 0.70, 0.80, 0.90]:
    p = (s >= t).astype(int)
    pr = precision_score(y, p, zero_division=0)
    re = recall_score(y, p, zero_division=0)
    f1 = f1_score(y, p, zero_division=0)

    print(f"{t:<12.2f}{pr*100:<15.2f}{re*100:<15.2f}{f1*100:<15.2f}")