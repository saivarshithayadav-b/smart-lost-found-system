from sentence_transformers import SentenceTransformer, util
from datasets import load_dataset
from scipy.stats import pearsonr, spearmanr


MODEL_NAME = "all-MiniLM-L6-v2"


def evaluate_sts():

    print("===================================")
    print("Starting STS Benchmark Evaluation")
    print("===================================")

    print("\n1. Loading SBERT model...")

    model = SentenceTransformer(MODEL_NAME)

    print("SBERT loaded successfully.")

    print("\n2. Loading STS Benchmark dataset...")

    dataset = load_dataset(
        "sentence-transformers/stsb",
        split="test"
    )

    print("STS dataset loaded successfully.")
    print("Number of test samples:", len(dataset))

    print("\n3. Reading sentence pairs...")

    sentence1 = dataset["sentence1"]
    sentence2 = dataset["sentence2"]
    scores = dataset["score"]

    print("Sentence pairs loaded.")

    print("\n4. Generating SBERT embeddings...")

    embeddings1 = model.encode(
        sentence1,
        convert_to_tensor=True,
        show_progress_bar=True
    )

    embeddings2 = model.encode(
        sentence2,
        convert_to_tensor=True,
        show_progress_bar=True
    )

    print("Embeddings generated successfully.")

    print("\n5. Calculating semantic similarity...")

    predicted_scores = util.cos_sim(
        embeddings1,
        embeddings2
    ).diagonal()

    predicted_scores = predicted_scores.cpu().numpy()

    print("Similarity scores calculated.")

    print("\n6. Calculating evaluation metrics...")

    pearson_score = pearsonr(
        scores,
        predicted_scores
    )[0]

    spearman_score = spearmanr(
        scores,
        predicted_scores
    )[0]

    print("\n===================================")
    print("       STS BENCHMARK RESULTS")
    print("===================================")

    print(
        "Pearson Correlation :",
        round(pearson_score, 4)
    )

    print(
        "Spearman Correlation:",
        round(spearman_score, 4)
    )

    print("===================================")

    print("\nEvaluation completed successfully.")


if __name__ == "__main__":
    evaluate_sts()