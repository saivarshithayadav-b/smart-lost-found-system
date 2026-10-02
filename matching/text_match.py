from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load pretrained SBERT model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def normalize_text(value):
    """
    Convert text into a standard format.
    """

    if value is None:
        return ""

    return str(value).strip()


def text_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts
    using pretrained SBERT embeddings.

    Returns:
        value between 0.0 and 1.0
    """

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    embedding1 = model.encode([text1])
    embedding2 = model.encode([text2])

    similarity = cosine_similarity(
        embedding1,
        embedding2
    )[0][0]

    # Keep result within 0–1
    similarity = max(
        0.0,
        min(1.0, similarity)
    )

    return round(
        float(similarity),
        4
    )