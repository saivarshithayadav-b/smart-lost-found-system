from PIL import Image, UnidentifiedImageError
import os
import torch
from transformers import CLIPProcessor, CLIPModel


# =========================================================
# LOAD PRETRAINED CLIP MODEL
# =========================================================

MODEL_NAME = "openai/clip-vit-base-patch32"

model = CLIPModel.from_pretrained(
    MODEL_NAME
)

processor = CLIPProcessor.from_pretrained(
    MODEL_NAME
)

model.eval()


# =========================================================
# IMAGE SIMILARITY
# =========================================================

def image_similarity(image1_path, image2_path):
    """
    Compare two images using pretrained CLIP.

    Returns:
        Similarity score between 0.0 and 1.0.
        Returns 0.0 if an image cannot be loaded.
    """

    # -----------------------------------------------------
    # VALIDATE IMAGE PATHS
    # -----------------------------------------------------

    if not image1_path or not image2_path:
        return 0.0

    if not os.path.isfile(image1_path):
        print("CLIP ERROR: Image not found:", image1_path)
        return 0.0

    if not os.path.isfile(image2_path):
        print("CLIP ERROR: Image not found:", image2_path)
        return 0.0

    # -----------------------------------------------------
    # LOAD IMAGES
    # -----------------------------------------------------

    try:
        image1 = Image.open(
            image1_path
        ).convert("RGB")

        image2 = Image.open(
            image2_path
        ).convert("RGB")

    except (UnidentifiedImageError, OSError) as error:
        print("CLIP ERROR: Could not open image:", error)
        return 0.0

    # -----------------------------------------------------
    # PREPROCESS IMAGES
    # -----------------------------------------------------

    try:
        inputs = processor(
            images=[image1, image2],
            return_tensors="pt"
        )

        # -------------------------------------------------
        # GENERATE IMAGE FEATURES
        # -------------------------------------------------

        with torch.no_grad():

            image_features = model.get_image_features(
                pixel_values=inputs["pixel_values"]
            )

        # Handle Transformers output object
        if hasattr(
            image_features,
            "pooler_output"
        ):
            image_features = (
                image_features.pooler_output
            )

        # -------------------------------------------------
        # NORMALIZE EMBEDDINGS
        # -------------------------------------------------

        image_features = (
            image_features /
            image_features.norm(
                dim=-1,
                keepdim=True
            ).clamp(min=1e-12)
        )

        # -------------------------------------------------
        # COSINE SIMILARITY
        # -------------------------------------------------

        similarity = torch.matmul(
            image_features[0],
            image_features[1]
        )

        # -------------------------------------------------
        # CONVERT -1 TO 1 RANGE INTO 0 TO 1
        # -------------------------------------------------

        similarity = (
            similarity + 1
        ) / 2

        # Keep score safely within 0–1
        similarity = torch.clamp(
            similarity,
            0.0,
            1.0
        )

        # -------------------------------------------------
        # RETURN SCORE
        # -------------------------------------------------

        return round(
            float(similarity.item()),
            4
        )

    except Exception as error:
        print(
            "CLIP ERROR: Image comparison failed:",
            error
        )
        return 0.0