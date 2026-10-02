from matching.image_match import image_similarity


image1 = "uploads/Screenshot_2026-09-24_at_6.47.38_PM.png"

image2 = "uploads/Screenshot_2026-09-24_at_7.02.55_PM.png"


score = image_similarity(image1, image2)


print("\nCLIP Image Similarity")
print("Image 1:", image1)
print("Image 2:", image2)
print("Similarity Score:", score)