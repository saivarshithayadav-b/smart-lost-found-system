
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache


@lru_cache(maxsize=1)
def load_sbert_model():
    """Load SBERT only when text matching is requested."""
    print("Loading SBERT model...")

    model = SentenceTransformer(
        "all-MiniLM-L6-v2",
        device="cpu"
    )

    print("SBERT model loaded successfully.")

    return model


def normalize_text(value):
    """Convert text into a standard format."""
    if value is None:
        return ""

    return str(value).strip()


def text_similarity(text1, text2):
    """
    Calculate semantic similarity using pretrained SBERT.
    Returns a value between 0.0 and 1.0.
    """

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0.0

    try:
        model = load_sbert_model()

        embeddings = model.encode([text1, text2])

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        similarity = max(
            0.0,
            min(1.0, float(similarity))
        )

        return round(similarity, 4)

    except Exception as error:
        print("SBERT ERROR: Text comparison failed:", error)
        return 0.0
