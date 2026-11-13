
from PIL import Image, UnidentifiedImageError
import os
import torch
from transformers import CLIPProcessor, CLIPModel
from functools import lru_cache

MODEL_NAME = "openai/clip-vit-base-patch32"


@lru_cache(maxsize=1)
def load_clip_model():
    """Load CLIP only when image matching is requested."""
    print("Loading CLIP model...")

    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)

    model.to("cpu")
    model.eval()

    print("CLIP model loaded successfully.")

    return model, processor


def image_similarity(image1_path, image2_path):
    """
    Compare two images using pretrained CLIP.
    Returns a similarity score between 0.0 and 1.0.
    """

    if not image1_path or not image2_path:
        return 0.0

    if not os.path.isfile(image1_path):
        print("CLIP ERROR: Image not found:", image1_path)
        return 0.0

    if not os.path.isfile(image2_path):
        print("CLIP ERROR: Image not found:", image2_path)
        return 0.0

    try:
        image1 = Image.open(image1_path).convert("RGB")
        image2 = Image.open(image2_path).convert("RGB")

    except (UnidentifiedImageError, OSError) as error:
        print("CLIP ERROR: Could not open image:", error)
        return 0.0

    try:
        model, processor = load_clip_model()

        inputs = processor(
            images=[image1, image2],
            return_tensors="pt"
        )

        with torch.no_grad():
            image_features = model.get_image_features(
                pixel_values=inputs["pixel_values"]
            )

        if hasattr(image_features, "pooler_output"):
            image_features = image_features.pooler_output

        image_features = (
            image_features /
            image_features.norm(
                dim=-1,
                keepdim=True
            ).clamp(min=1e-12)
        )

        similarity = torch.matmul(
            image_features[0],
            image_features[1]
        )

        similarity = (similarity + 1) / 2
        similarity = torch.clamp(similarity, 0.0, 1.0)

        return round(float(similarity.item()), 4)

    except Exception as error:
        print("CLIP ERROR: Image comparison failed:", error)
        return 0.0
