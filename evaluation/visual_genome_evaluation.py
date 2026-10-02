from datasets import load_dataset
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch


MODEL_NAME = "openai/clip-vit-base-patch32"

# Keep this small initially.
# Visual Genome is a very large dataset.
NUM_SAMPLES = 100


def evaluate_visual_genome():

    print("===================================")
    print("Visual Genome + CLIP Evaluation")
    print("===================================")

    print("\n1. Loading CLIP model...")

    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)

    model.eval()

    print("CLIP loaded successfully.")

    print("\n2. Loading Visual Genome dataset...")

    dataset = load_dataset(
        "ranjaykrishna/visual_genome",
        "region_descriptions_v1.0.0",
        split="train"
    )

    print("Visual Genome loaded successfully.")
    print("Total images:", len(dataset))

    total = min(NUM_SAMPLES, len(dataset))

    print(
        "Samples used for evaluation:",
        total
    )

    correct = 0
    processed = 0

    print("\n3. Evaluating CLIP...")

    for index in range(total):

        sample = dataset[index]

        image = sample["image"]

        regions = sample["regions"]

        if image is None or not regions:
            continue

        # Take the first region description.
        phrase = regions[0]["phrase"]

        if not phrase:
            continue

        inputs = processor(
            text=[phrase],
            images=image,
            return_tensors="pt",
            padding=True
        )

        with torch.no_grad():

            outputs = model(**inputs)

            logits = outputs.logits_per_image

            probability = logits.softmax(
                dim=1
            )[0][0].item()

        # Since there is only one text candidate,
        # this measures CLIP's image-text compatibility,
        # not classification accuracy.

        print(
            f"Sample {index + 1}: "
            f"CLIP score = {probability:.4f}"
        )

        processed += 1

    print("\n===================================")
    print("VISUAL GENOME EVALUATION COMPLETE")
    print("===================================")

    print(
        "Processed samples:",
        processed
    )

    print(
        "\nNote:"
    )

    print(
        "This evaluation checks CLIP's "
        "image-text compatibility using "
        "Visual Genome region descriptions."
    )

    print(
        "It does NOT fine-tune or modify CLIP."
    )

    print("===================================")


if __name__ == "__main__":
    evaluate_visual_genome()