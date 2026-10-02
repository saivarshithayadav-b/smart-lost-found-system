from database import get_db_connection
from matching.database_matching import match_lost_item


# Get Lost Item #7 directly from MySQL
connection = get_db_connection()
cursor = connection.cursor(dictionary=True)

cursor.execute("""
    SELECT *
    FROM lost_items
    WHERE id = 7
""")

lost_item = cursor.fetchone()

cursor.close()
connection.close()


print("\n==============================")
print("DATABASE MATCHING TEST")
print("==============================")

print("Lost Item ID:", lost_item["id"])
print("Item:", lost_item["item_name"])
print("Category:", lost_item["category"])
print("Color:", lost_item["color"])
print("Brand:", lost_item["brand"])
print("Location:", lost_item["location"])
print("Latitude:", lost_item["latitude"])
print("Longitude:", lost_item["longitude"])
print("Image:", lost_item["image_path"])


# Run complete matching
results = match_lost_item(
    lost_item,
    radius_km=5
)


print("\n==============================")
print("MATCHING RESULTS")
print("==============================")

print("Total Candidates:", len(results))


for result in results:

    print("\n------------------------------")

    print("Found Item ID:", result["found_item_id"])
    print("Found Item:", result["found_item_name"])
    print("Distance:", result["distance_km"], "km")

    print("\nMetadata Scores:")
    print("Category:", result["category_score"])
    print("Color:", result["color_score"])
    print("Brand:", result["brand_score"])
    print("Date:", result["date_score"])
    print("Metadata:", result["metadata_score"])

    print("\nAI Scores:")
    print("Text:", result["text_score"])
    print("Image:", result["image_score"])

    print("\nFinal Score:", result["final_score"])
    print("Threshold:", result["threshold"])
    print("Decision:", result["decision"])