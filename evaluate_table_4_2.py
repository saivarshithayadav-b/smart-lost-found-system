import csv
import getpass
import os
import mysql.connector
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from matching.metadata_match import match_metadata
from matching.text_match import text_similarity
from matching.image_match import image_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
THRESHOLD = 0.70

def image_path(name):
    if not name:
        return None
    return os.path.join(UPLOAD_DIR, os.path.basename(name))

def main():
    password = getpass.getpass("MySQL password for root: ")
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password=password,
        database="lost_found_db"
    )

    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT id, item_name, category, description, color, brand,
               lost_date, image_path
        FROM lost_items
        ORDER BY id
    """)
    lost_items = cur.fetchall()

    cur.execute("""
        SELECT id, item_name, category, description, color, brand,
               found_date, image_path
        FROM found_items
        ORDER BY id
    """)
    found_items = cur.fetchall()

    cur.close()
    db.close()

    rows = []
    total = len(lost_items) * len(found_items)
    print(f"\nEvaluating {len(lost_items)} lost items x "
          f"{len(found_items)} found items = {total} pairs.")
    print("Loading/computing model scores. This may take a while.\n")

    for i, lost in enumerate(lost_items, 1):
        for found in found_items:
            actual = int(lost["id"] == 33 and found["id"] == 27)

            meta = match_metadata(lost, found)["metadata_score"]
            text = text_similarity(
                lost.get("description"),
                found.get("description")
            )

            lost_img = image_path(lost.get("image_path"))
            found_img = image_path(found.get("image_path"))

            if lost_img and found_img and os.path.isfile(lost_img) and os.path.isfile(found_img):
                clip = image_similarity(lost_img, found_img)
            else:
                clip = 0.0

            scores = {
                "Metadata only": meta,
                "SBERT only": text,
                "CLIP only": clip,
                "Metadata + SBERT": (meta + text) / 2,
                "Metadata + CLIP": (meta + clip) / 2,
                "Metadata + SBERT + CLIP": 0.30 * meta + 0.35 * text + 0.35 * clip
            }

            row = {
                "lost_id": lost["id"],
                "found_id": found["id"],
                "actual_match": actual,
                "metadata_score": meta,
                "sbert_score": text,
                "clip_score": clip
            }

            for method, score in scores.items():
                key = method.lower().replace(" + ", "_").replace(" ", "_")
                row[key + "_score"] = round(float(score), 4)
                row[key + "_predicted"] = int(score >= THRESHOLD)

            rows.append(row)

        print(f"Completed lost item {i}/{len(lost_items)} (ID {lost['id']}).")

    csv_path = os.path.join(BASE_DIR, "table_4_2_evaluation_pairs.csv")
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    methods = [
        ("Metadata only", "metadata_only_predicted"),
        ("SBERT only", "sbert_only_predicted"),
        ("CLIP only", "clip_only_predicted"),
        ("Metadata + SBERT", "metadata_sbert_predicted"),
        ("Metadata + CLIP", "metadata_clip_predicted"),
        ("Metadata + SBERT + CLIP", "metadata_sbert_clip_predicted")
    ]

    y_true = [r["actual_match"] for r in rows]
    print("\nTABLE 4.2 RESULTS (threshold = 0.70)")
    print("-" * 78)
    print(f"{'Matching method':30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1-score':>10}")
    print("-" * 78)

    for name, pred_key in methods:
        y_pred = [r[pred_key] for r in rows]
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        print(f"{name:30} {acc * 100:9.2f}% {prec * 100:9.2f}% "
              f"{rec * 100:9.2f}% {f1 * 100:9.2f}%")

    print(f"\nTotal pairs: {len(rows)}")
    print("Positive labels: 1 (Lost ID 33 -> Found ID 27)")
    print(f"Negative labels: {len(rows) - 1} (all other pairs, as confirmed)")
    print(f"Results saved to: {csv_path}")
    print("\nNOTE: These metrics use one positive pair and all other pairs as negatives.")
    print("They are preliminary and depend on the correctness of those labels.")

if __name__ == "__main__":
    main()
